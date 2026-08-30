import os
import secrets
import time

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import RedirectResponse
from svix.webhooks import Webhook

from . import client, oauth, rules, store
from save_meeting import save_meeting

router = APIRouter()

DEFAULT_BOT_NAME = "WhatsON_meeting Notetaker"

# Délai (en secondes) pendant lequel l'enregistrement est mis en pause dès qu'il démarre,
# pour laisser le temps aux participants qui ne souhaitent pas être enregistrés de quitter
# la réunion. La portion en pause est exclue du recap final (audio, transcript, diarisation).
RECORDING_DELAY_SECONDS = 3 * 60
RECORDING_DELAY_MINUTES = RECORDING_DELAY_SECONDS // 60

RGPD_ENTRY_MESSAGE = (
    f"RGPD : cette réunion est enregistrée par WhatsON_meeting afin d'en générer un compte-rendu. "
    f"Vous disposez de {RECORDING_DELAY_MINUTES} minutes avant le début de l'enregistrement : "
    f"si vous ne souhaitez pas être enregistré·e, merci de quitter la réunion avant la fin de ce délai."
)
RECORDING_PAUSE_MESSAGE = (
    f"⏸Enregistrement en pause pendant {RECORDING_DELAY_MINUTES} minutes pour vous laisser le temps de "
    f"rejoindre. Si vous ne souhaitez pas être enregistré·e, c'est le moment de quitter."
)
RECORDING_RESUME_MESSAGE = "L'enregistrement commence maintenant dans la réunion."


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


def _delay_recording_start(bot_id: str) -> None:
    """Coupe l'enregistrement dès qu'il démarre, attend RECORDING_DELAY_SECONDS, puis le
    reprend (tâche de fond, déclenchée sur le premier statut 'in_call_recording')."""
    try:
        client.pause_bot_recording(bot_id, chat_message=RECORDING_PAUSE_MESSAGE)
        print(f"[webhook] enregistrement mis en pause pour bot {bot_id} ({RECORDING_DELAY_SECONDS}s)")
    except Exception as exc:
        print(f"[webhook] échec de la mise en pause pour bot {bot_id} : {exc}")
        return

    time.sleep(RECORDING_DELAY_SECONDS)

    try:
        client.resume_bot_recording(bot_id, chat_message=RECORDING_RESUME_MESSAGE)
        print(f"[webhook] enregistrement repris pour bot {bot_id}")
    except Exception as exc:
        print(f"[webhook] échec de la reprise d'enregistrement pour bot {bot_id} : {exc}")

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
    event_data = payload.get("data", {})

    if event in ("calendar.event_created", "calendar.event_updated"):
        calendar_id = event_data.get("calendar_id")
        series_id = event_data.get("series_id")

        for instance in event_data.get("instances", []):
            event_id = instance.get("event_id")
            if not event_id or store.is_event_scheduled(event_id):
                print(f"[webhook] event {event_id} ignoré (déjà programmé ou sans id)")
                continue

            calendar_event = client.get_event(calendar_id, event_id)
            should_bot_join = rules.should_join(calendar_event)
            print(f"[webhook] event {event_id} '{calendar_event.get('title')}' -> should_join={should_bot_join}")
            if should_bot_join:
                client.schedule_bot(
                    calendar_id, event_id, series_id,
                    bot_name=DEFAULT_BOT_NAME,
                    entry_message=RGPD_ENTRY_MESSAGE,
                )
                store.mark_event_scheduled(event_id)

                attendees = calendar_event.get("attendees") or []
                emails = [attendee.get("email") for attendee in attendees if attendee.get("email")]
                store.save_event_emails(event_id, emails)

                print(f"[webhook] bot programmé pour event {event_id}")

        return {"status": "ok"}

    if event == "bot.status_change":
        bot_id = event_data.get("bot_id")
        event_id = event_data.get("event_id")
        status_code = (event_data.get("status") or {}).get("code")
        print(f"[webhook] bot {bot_id} -> status={status_code}")

        if status_code == "in_call_recording" and bot_id and not store.is_recording_delay_started(bot_id):
            # Premier démarrage réel de l'enregistrement : on coupe tout de suite pour
            # laisser le temps RGPD (RECORDING_DELAY_SECONDS) avant de vraiment enregistrer.
            store.mark_recording_delay_started(bot_id)
            background_tasks.add_task(_delay_recording_start, bot_id)

        if status_code == "call_ended":
            # MeetingBaaS n'envoie pas de webhook dédié à la fin de la transcription
            # (observé : les status_change s'arrêtent à "transcribing") : on la
            # poll nous-mêmes en tâche de fond dès que le bot a quitté l'appel.
            background_tasks.add_task(_process_completed_bot, bot_id, event_id)
        return {"status": "ok"}

    return {"status": "ignored"}
