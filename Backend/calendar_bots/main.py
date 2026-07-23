import os
import secrets

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from svix.webhooks import Webhook

from . import client, oauth, rules, store

router = APIRouter()

# CSRF sur le callback OAuth : mono-utilisateur pour l'instant donc une seule
# valeur en mémoire suffit (voir store.py pour le même choix de scope).
_pending_state = {"value": None}


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
    store.save_connection(calendar_uuid, google_calendar_id="primary")

    return {"status": "ok", "message": "Calendrier connecté."}


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

    return {"status": "ok"}
