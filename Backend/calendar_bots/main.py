import os
import secrets

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import RedirectResponse
from svix.webhooks import Webhook

from . import client, oauth, rules, store
from save_meeting import save_meeting

router = APIRouter()

DEFAULT_BOT_NAME = "Scribe Notetaker"


def _process_completed_bot(bot_id: str, event_id: str | None = None) -> None:
    """Attend la transcription puis enregistre le recap en base (tâche de fond,
    déclenchée dès que le bot a quitté l'appel)."""
    if not bot_id or store.is_bot_saved(bot_id) or store.is_bot_processing(bot_id):
        print(f"[webhook] bot {bot_id} ignoré (déjà traité/en cours, ou sans id)")
        return
    store.mark_bot_processing(bot_id)

    try:
        result = client.wait_for_transcription(bot_id)
        emails = store.get_event_emails(event_id)
        saved = save_meeting(result, bot_name=DEFAULT_BOT_NAME, source="visio", emails=emails)
        store.mark_bot_saved(bot_id)
        print(f"[webhook] recap enregistré en base pour bot {bot_id} (id={saved['id']}).")
    except Exception as exc:
        print(f"[webhook] échec de l'enregistrement du recap pour bot {bot_id} : {exc}")

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
async def webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()

    webhook_secret = os.environ.get("MEETING_BAAS_WEBHOOK_SECRET")
    if webhook_secret:
        try:
            Webhook(webhook_secret).verify(body, dict(request.headers))
        except Exception:
            raise HTTPException(status_code=401, detail="Signature de webhook invalide.")

    payload = await request.json()
    event = payload.get("event")
    print(f"[webhook] reçu: {event}")
    data = payload.get("data", {})

    if event in ("calendar.event_created", "calendar.event_updated"):
        calendar_id = data.get("calendar_id")
        series_id = data.get("series_id")

        for instance in data.get("instances", []):
            event_id = instance.get("event_id")
            if not event_id or store.is_event_scheduled(event_id):
                print(f"[webhook] event {event_id} ignoré (déjà programmé ou sans id)")
                continue

            calendar_event = client.get_event(calendar_id, event_id)
            joins = rules.should_join(calendar_event)
            print(f"[webhook] event {event_id} '{calendar_event.get('title')}' -> should_join={joins}")
            if joins:
                client.schedule_bot(calendar_id, event_id, series_id, bot_name=DEFAULT_BOT_NAME)
                store.mark_event_scheduled(event_id)

                attendees = calendar_event.get("attendees") or []
                emails = [a.get("email") for a in attendees if a.get("email")]
                store.save_event_emails(event_id, emails)

                print(f"[webhook] bot programmé pour event {event_id}")

        return {"status": "ok"}

    if event == "bot.status_change":
        bot_id = data.get("bot_id")
        event_id = data.get("event_id")
        status = (data.get("status") or {}).get("code")
        print(f"[webhook] bot {bot_id} -> status={status}")
        if status == "call_ended":
            # MeetingBaaS n'envoie pas de webhook dédié à la fin de la transcription
            # (observé : les status_change s'arrêtent à "transcribing") : on la
            # poll nous-mêmes en tâche de fond dès que le bot a quitté l'appel.
            background_tasks.add_task(_process_completed_bot, bot_id, event_id)
        return {"status": "ok"}

    return {"status": "ignored"}
