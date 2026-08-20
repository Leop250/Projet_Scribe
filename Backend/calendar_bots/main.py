import os
import secrets

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from svix.webhooks import Webhook

from . import client, google_calendar, oauth, rules, store

router = APIRouter()

# CSRF sur le callback OAuth : mono-utilisateur pour l'instant donc une seule
# valeur en mémoire suffit (voir store.py pour le même choix de scope).
_pending_state = {"value": None}

# CSRF sur le sign-in participant : potentiellement plusieurs visiteurs en même
# temps (des events différents), donc un ensemble plutôt qu'une valeur unique.
_pending_signin_nonces = set()


@router.get("/oauth/authorize")
async def authorize(request: Request):
    redirect_uri = str(request.url_for("oauth_callback"))
    state = secrets.token_urlsafe(16)
    _pending_state["value"] = state
    return RedirectResponse(oauth.build_authorize_url(redirect_uri, state))


@router.get("/oauth/callback", name="oauth_callback")
async def oauth_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Autorisation Google refusée : {error}")
    if not code or not state or state != _pending_state["value"]:
        raise HTTPException(status_code=400, detail="État OAuth invalide ou expiré, relance /calendar/oauth/authorize.")
    _pending_state["value"] = None

    redirect_uri = str(request.url_for("oauth_callback"))
    refresh_token = oauth.exchange_code_for_refresh_token(code, redirect_uri)
    calendar_uuid = client.register_calendar(refresh_token)
    store.save_connection(calendar_uuid, google_calendar_id="primary", refresh_token=refresh_token)

    return {"status": "ok", "message": "Calendrier connecté."}


@router.get("/join/signin/callback", name="join_signin_callback")
async def join_signin_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Connexion Google refusée : {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Requête invalide.")

    try:
        nonce, consent, calendar_id, event_id = state.split(".", 3)
    except ValueError:
        raise HTTPException(status_code=400, detail="État invalide.")
    if nonce not in _pending_signin_nonces:
        raise HTTPException(status_code=400, detail="État expiré ou déjà utilisé, relance depuis l'invitation.")
    _pending_signin_nonces.discard(nonce)

    redirect_uri = str(request.url_for("join_signin_callback"))
    email = oauth.get_verified_email(code, redirect_uri)

    store.record_consent(
        event_id, accepted=(consent == "yes"), email=email,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", ""),
    )

    if consent == "yes":
        event = client.get_event(calendar_id, event_id)
        meeting_url = event.get("meeting_url")
        if not meeting_url:
            raise HTTPException(status_code=404, detail="Aucun lien de réunion pour cet événement.")
        return RedirectResponse(meeting_url)

    return HTMLResponse(_page(
        "Consentement refusé",
        "<p>Vous ne rejoindrez pas la réunion. Aucune donnée n'est enregistrée.</p>",
    ))


@router.get("/join/{calendar_id}/{event_id}/signin")
async def join_signin(request: Request, calendar_id: str, event_id: str, consent: str):
    nonce = secrets.token_urlsafe(12)
    _pending_signin_nonces.add(nonce)
    state = f"{nonce}.{consent}.{calendar_id}.{event_id}"
    redirect_uri = str(request.url_for("join_signin_callback"))
    return RedirectResponse(oauth.build_signin_url(redirect_uri, state))


@router.get("/join/{calendar_id}/{event_id}")
async def join(calendar_id: str, event_id: str):
    event = client.get_event(calendar_id, event_id)

    return HTMLResponse(_page(
        "Consentement à l'enregistrement",
        f"""
        <p>La réunion « {event.get('title', '')} » est enregistrée et transcrite automatiquement par Scribe.</p>
        <p>En rejoignant, vous acceptez que votre voix soit enregistrée et transcrite.</p>
        <a class="btn btn-accept" href="/calendar/join/{calendar_id}/{event_id}/signin?consent=yes">Continuer avec Google et rejoindre</a>
        <a class="btn btn-decline" href="/calendar/join/{calendar_id}/{event_id}/signin?consent=no">Je refuse</a>
        """,
    ))


def _page(title, body):
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
  body {{ font-family: sans-serif; max-width: 480px; margin: 80px auto; text-align: center; }}
  .btn {{ display: inline-block; margin: 8px; padding: 12px 24px; text-decoration: none; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; }}
  .btn-accept {{ background: #4f46e5; color: white; }}
  .btn-decline {{ background: #e5e7eb; color: #111; }}
</style></head>
<body><h1>{title}</h1>{body}</body></html>"""


@router.post("/webhook")
async def webhook(request: Request):
    body = await request.body()

    webhook_secret = os.environ.get("MEETING_BAAS_WEBHOOK_SECRET")
    if webhook_secret:
        try:
            Webhook(webhook_secret).verify(body, dict(request.headers))
        except Exception:
            raise HTTPException(status_code=401, detail="Signature de webhook invalide.")

    payload = await request.json()
    print(f"[webhook] reçu: {payload.get('event')}")
    if payload.get("event") not in ("calendar.event_created", "calendar.event_updated"):
        return {"status": "ignored"}

    data = payload.get("data", {})
    calendar_id = data.get("calendar_id")
    series_id = data.get("series_id")

    for instance in data.get("instances", []):
        event_id = instance.get("event_id")
        if not event_id or store.is_event_scheduled(event_id):
            print(f"[webhook] event {event_id} ignoré (déjà programmé ou sans id)")
            continue

        event = client.get_event(calendar_id, event_id)
        joins = rules.should_join(event)
        print(f"[webhook] event {event_id} '{event.get('title')}' -> should_join={joins}")
        if joins:
            client.schedule_bot(calendar_id, event_id, series_id)
            store.mark_event_scheduled(event_id)
            print(f"[webhook] bot programmé pour event {event_id}")

            connection = store.get_connection()
            google_event_id = event.get("raw_payload", {}).get("id")
            if connection and google_event_id:
                redirect_url = f"{os.environ['PUBLIC_BASE_URL']}/calendar/join/{calendar_id}/{event_id}"
                google_calendar.add_consent_redirect(
                    connection["refresh_token"], connection["google_calendar_id"], google_event_id, redirect_url,
                )
                print(f"[webhook] lien de consentement inséré: {redirect_url}")

    return {"status": "ok"}
