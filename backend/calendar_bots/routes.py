import os
import threading
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from auth.authentification import create_access_token, verify_token
from auth.dependencies import get_current_user
from auth.users import UserModel

from . import client, oauth, rules, store
from .save_meeting import save_meeting
from .scheduling import (
    DEFAULT_BOT_NAME,
    RECORDING_DELAY_SECONDS,
    RECORDING_PAUSE_MESSAGE,
    RECORDING_RESUME_MESSAGE,
    schedule_bot_for_event,
)

try:  # vérification de signature du webhook — optionnelle tant que svix n'est pas requis
    from svix.webhooks import Webhook
except ImportError:  # pragma: no cover
    Webhook = None

router = APIRouter()

_OAUTH_PURPOSE = "calendar_oauth"

UPCOMING_WINDOW_DAYS = 30
UPCOMING_MAX = 50

if not os.environ.get("GOOGLE_OAUTH_REDIRECT_URI"):
    print(
        "[calendar_bots] GOOGLE_OAUTH_REDIRECT_URI non défini : l'URI de redirection est "
        "déduite de chaque requête, risque de redirect_uri_mismatch derrière un proxy."
    )


def _run_in_background(func, *args) -> None:
    threading.Thread(target=func, args=args, daemon=True).start()


def _frontend_url() -> str:
    url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    if url and not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url.rstrip("/")


def _redirect_uri(request: Request) -> str:
    return os.environ.get("GOOGLE_OAUTH_REDIRECT_URI") or str(request.url_for("calendar_oauth_callback"))


def _error_redirect(frontend: str, reason: str) -> RedirectResponse:
    return RedirectResponse(f"{frontend}/settings?google=error&reason={reason}")


def _process_completed_bot(bot_id: str, event_id: str | None = None) -> None:
    """Attend la transcription puis enregistre le recap en base (tâche de fond,
    déclenchée dès que le bot a quitté l'appel)."""
    if not bot_id or store.is_bot_saved(bot_id) or store.is_bot_processing(bot_id):
        print(f"[calendar_bots] bot {bot_id} ignoré (déjà traité/en cours, ou sans id)")
        return
    store.mark_bot_processing(bot_id)
    try:
        result = client.wait_for_transcription(bot_id)
        emails = store.get_event_emails(event_id)
        saved = save_meeting(result, bot_name=DEFAULT_BOT_NAME, source="visio", emails=emails)
        store.mark_bot_saved(bot_id)
        print(f"[calendar_bots] recap enregistré pour bot {bot_id} (id={saved['id']}).")
    except Exception as exc:  # noqa: BLE001 - tâche de fond, on log et on abandonne
        print(f"[calendar_bots] échec de l'enregistrement du recap pour bot {bot_id} : {exc}")
        store.clear_bot_processing(bot_id)


def _delay_recording_start(bot_id: str) -> None:
    """Coupe l'enregistrement dès qu'il démarre, attend RECORDING_DELAY_SECONDS, puis le
    reprend (tâche de fond ; time.sleep bloque un worker du threadpool le temps du délai)."""
    try:
        client.pause_bot_recording(bot_id, chat_message=RECORDING_PAUSE_MESSAGE)
        print(f"[calendar_bots] enregistrement en pause pour bot {bot_id} ({RECORDING_DELAY_SECONDS}s)")
    except Exception as exc:  # noqa: BLE001
        print(f"[calendar_bots] échec de la mise en pause pour bot {bot_id} : {exc}")
        return

    time.sleep(RECORDING_DELAY_SECONDS)

    try:
        client.resume_bot_recording(bot_id, chat_message=RECORDING_RESUME_MESSAGE)
        print(f"[calendar_bots] enregistrement repris pour bot {bot_id}")
    except Exception as exc:  # noqa: BLE001
        print(f"[calendar_bots] échec de la reprise d'enregistrement pour bot {bot_id} : {exc}")


@router.get("/oauth/authorize")
def authorize(request: Request, current_user: UserModel = Depends(get_current_user)):
    state = create_access_token(data={"sub": str(current_user.id), "purpose": _OAUTH_PURPOSE})
    return {"authorize_url": oauth.build_authorize_url(_redirect_uri(request), state)}


@router.get("/oauth/callback", name="calendar_oauth_callback")
def oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    frontend = _frontend_url()
    if error:
        return _error_redirect(frontend, "oauth_denied")
    if not code or not state:
        return _error_redirect(frontend, "missing_params")

    try:
        payload = verify_token(state)
        if payload.get("purpose") != _OAUTH_PURPOSE:
            raise ValueError("purpose invalide")
        user_id = int(payload["sub"])
    except (HTTPException, ValueError, KeyError, TypeError):
        return _error_redirect(frontend, "bad_state")

    try:
        tokens = oauth.exchange_code_for_tokens(code, _redirect_uri(request))
        google_email = oauth.fetch_google_email(tokens.get("access_token", ""))
        calendar_uuid = client.register_calendar(tokens["refresh_token"], google_email=google_email)
    except Exception as exc:  # noqa: BLE001
        print(f"[calendar_bots] échec de la connexion calendrier : {exc}")
        message = str(exc)
        if "FST_ERR_CALENDAR_CONNECTION_LIMIT_EXCEEDED" in message:
            reason = "mb_limit"
        elif "refresh_token" in message:
            reason = "no_refresh_token"
        else:
            reason = "connect_failed"
        return _error_redirect(frontend, reason)

    store.save_connection(user_id, calendar_uuid, google_calendar_id="primary", google_email=google_email)
    return RedirectResponse(f"{frontend}/settings?google=connected")


@router.get("/status")
def status(current_user: UserModel = Depends(get_current_user)):
    connection = store.get_connection(current_user.id)
    if connection is None:
        return {"connected": False}
    return {
        "connected": True,
        "email": connection["google_email"] or connection["google_calendar_id"],
        "last_sync_at": connection["connected_at"],
    }


def _serialize_event(event: dict) -> dict:
    attendees = event.get("attendees") or []
    return {
        "id": event.get("event_id") or event.get("id"),
        "title": (event.get("title") or "").strip() or "Sans titre",
        "start": event.get("start_time"),
        "end": event.get("end_time"),
        "attendees": [a.get("email") for a in attendees if isinstance(a, dict) and a.get("email")],
        "meeting_url": event.get("meeting_url"),
        "will_record": bool(event.get("bot_scheduled")) or rules.should_join(event),
    }


@router.get("/events")
def upcoming_events(current_user: UserModel = Depends(get_current_user)):
    connection = store.get_connection(current_user.id)
    if connection is None:
        return {"connected": False, "events": []}

    now = datetime.now(timezone.utc)
    try:
        raw = client.list_events(
            connection["meetingbaas_calendar_uuid"],
            now.isoformat(),
            (now + timedelta(days=UPCOMING_WINDOW_DAYS)).isoformat(),
        )
    except Exception as exc:  # noqa: BLE001 - on renvoie une liste vide plutôt qu'un 500
        print(f"[calendar_bots] échec de la récupération des events : {exc}")
        return {"connected": True, "events": [], "error": "fetch_failed"}

    cutoff = now.isoformat()
    events = [_serialize_event(event) for event in (raw or [])]
    events = [event for event in events if event["start"] and event["start"] >= cutoff]
    events.sort(key=lambda event: event["start"])
    return {"connected": True, "events": events[:UPCOMING_MAX]}


@router.delete("")
def disconnect(current_user: UserModel = Depends(get_current_user)):
    calendar_uuid = store.delete_connection(current_user.id)
    if calendar_uuid is None:
        return {"message": "Aucune connexion calendrier à supprimer."}
    try:
        client.delete_calendar(calendar_uuid)
    except Exception as exc:  # noqa: BLE001 - la connexion locale est déjà supprimée
        print(f"[calendar_bots] suppression MeetingBaaS ignorée : {exc}")
    return {"message": "Connexion calendrier supprimée."}


@router.post("/webhook")
async def webhook(request: Request):
    body = await request.body()

    webhook_secret = os.environ.get("MEETING_BAAS_WEBHOOK_SECRET")
    allow_unsigned = os.environ.get("ALLOW_UNSIGNED_WEBHOOK") == "1"
    if webhook_secret and Webhook is not None:
        try:
            Webhook(webhook_secret).verify(body, dict(request.headers))
        except Exception:
            raise HTTPException(status_code=401, detail="Signature de webhook invalide.")
    elif not allow_unsigned:
        raise HTTPException(status_code=503, detail="Webhook non configuré : signature requise.")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Corps de webhook invalide.")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Corps de webhook invalide.")

    event = payload.get("event")
    event_data = payload.get("data", {})
    print(f"[calendar_bots] webhook reçu: {event}")

    if event in ("calendar.event_created", "calendar.event_updated"):
        calendar_id = event_data.get("calendar_id")
        series_id = event_data.get("series_id")

        for instance in event_data.get("instances", []):
            event_id = instance.get("event_id")
            if not event_id or store.is_event_scheduled(event_id):
                continue

            calendar_event = client.get_event(calendar_id, event_id)
            if not rules.should_join(calendar_event):
                continue

            try:
                scheduled = schedule_bot_for_event(
                    calendar_id, event_id, series_id, calendar_event.get("attendees")
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[calendar_bots] échec de programmation pour event {event_id} : {exc}")
                continue
            if scheduled:
                print(f"[calendar_bots] bot programmé pour event {event_id}")

        return {"status": "ok"}

    if event == "bot.status_change":
        bot_id = event_data.get("bot_id")
        event_id = event_data.get("event_id")
        status_code = (event_data.get("status") or {}).get("code")
        print(f"[calendar_bots] bot {bot_id} -> status={status_code}")

        if status_code == "in_call_recording" and bot_id and not store.is_recording_delay_started(bot_id):
            store.mark_recording_delay_started(bot_id)
            _run_in_background(_delay_recording_start, bot_id)

        if status_code == "call_ended":
            _run_in_background(_process_completed_bot, bot_id, event_id)

        return {"status": "ok"}

    return {"status": "ignored"}
