"""Wrapper fin autour de l'API v2 MeetingBaaS (Calendar API)."""

import os
import time

import httpx

BASE_URL = "https://api.meetingbaas.com/v2"
POLL_INTERVAL_SECONDS = 15
POLL_TIMEOUT_SECONDS = 20 * 60


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "x-meeting-baas-api-key": os.environ["MEETING_BAAS_API_KEY"],
    }


def _call(method: str, path: str, **kwargs):
    response = httpx.request(method, f"{BASE_URL}{path}", headers=_headers(), timeout=30, **kwargs)
    if not response.is_success:
        raise RuntimeError(f"MeetingBaaS {method} {path} -> {response.status_code}: {response.text}")
    body = response.json()
    # Les réponses MeetingBaaS semblent enveloppées dans {"success": ..., "data": ...}
    # (observé sur GET /calendars) : on déballe si cette forme est présente.
    return body["data"] if isinstance(body, dict) and "data" in body else body


def update_calendar_credentials(calendar_id: str, refresh_token: str):
    """PATCH /v2/calendars/{id} : fait tourner les credentials OAuth d'une connexion
    existante (ex: refresh_token expiré après 7j en mode Google "Testing"). MeetingBaaS
    revalide la connexion et recrée l'abonnement push automatiquement."""
    return _call(
        "PATCH",
        f"/calendars/{calendar_id}",
        json={
            "oauth_client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
            "oauth_client_secret": os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            "oauth_refresh_token": refresh_token,
        },
    )


def register_calendar(refresh_token: str, google_calendar_id: str = "primary") -> str:
    try:
        calendar_data = _call(
            "POST",
            "/calendars",
            json={
                "calendar_platform": "google",
                "oauth_client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
                "oauth_client_secret": os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
                "oauth_refresh_token": refresh_token,
                "raw_calendar_id": google_calendar_id,
            },
        )
    except RuntimeError as exc:
        if "FST_ERR_CALENDAR_CONNECTION_ALREADY_EXISTS" not in str(exc):
            raise
        # Mono-connexion côté MeetingBaaS : on récupère la connexion existante puis on
        # lui repousse le refresh_token qu'on vient d'obtenir — sans ça, une connexion
        # en erreur (refresh_token expiré) resterait cassée même après réautorisation.
        existing = _call("GET", "/calendars")[0]
        if not isinstance(existing, dict) or "calendar_id" not in existing:
            raise RuntimeError(f"Réponse MeetingBaaS inattendue (pas de champ 'calendar_id'): {existing}")
        calendar_data = update_calendar_credentials(existing["calendar_id"], refresh_token)

    if not isinstance(calendar_data, dict) or "calendar_id" not in calendar_data:
        raise RuntimeError(f"Réponse MeetingBaaS inattendue (pas de champ 'calendar_id'): {calendar_data}")
    return calendar_data["calendar_id"]


def delete_calendar(calendar_id: str) -> None:
    _call("DELETE", f"/calendars/{calendar_id}")


def get_event(calendar_id: str, event_id: str):
    return _call("GET", f"/calendars/{calendar_id}/events/{event_id}")


def schedule_bot(
    calendar_id: str,
    event_id: str,
    series_id: str | None,
    bot_name: str = "WhatsON_meeting Notetaker",
    entry_message: str | None = None,
):
    bot_data = _call(
        "POST",
        f"/calendars/{calendar_id}/bots",
        json={
            "event_id": event_id,
            "series_id": series_id,
            "all_occurrences": False,
            "bot_name": bot_name,
            "recording_mode": "audio_only",
            "transcription_enabled": True,
            "transcription_config": {"provider": "gladia"},
            # Posté dans le chat de la réunion dès que le bot rejoint (max 4096 caractères).
            "entry_message": entry_message,
        },
    )
    # MeetingBaaS renvoie une liste de bots (un par occurrence), même pour
    # all_occurrences=False : on ne prend que le premier.
    if isinstance(bot_data, list):
        if not bot_data:
            raise RuntimeError(f"MeetingBaaS n'a programmé aucun bot pour l'event {event_id}")
        bot_data = bot_data[0]
    return bot_data


def get_bot_status(bot_id: str):
    """État/résultat complet d'un bot (transcription, participants, ...), utilisé une
    fois la réunion terminée pour sauvegarder le recap."""
    return _call("GET", f"/bots/{bot_id}")


def pause_bot_recording(bot_id: str, chat_message: str | None = None):
    """POST /bots/{id}/pause-recording : le bot reste dans l'appel mais la portion en
    pause est exclue de l'enregistrement/transcript/diarisation final."""
    return _call("POST", f"/bots/{bot_id}/pause-recording", json={"chat_message": chat_message})


def resume_bot_recording(bot_id: str, chat_message: str | None = None):
    """POST /bots/{id}/resume-recording : reprend un enregistrement mis en pause."""
    return _call("POST", f"/bots/{bot_id}/resume-recording", json={"chat_message": chat_message})


# Statuts terminaux (enum "status" de GET /bots/{id}) qui signifient que le bot ne
# produira jamais de transcription.
FAILURE_STATUSES = {
    "failed",
    "transcription_failed",
    "recording_failed",
    "bot_rejected",
    "bot_removed",
    "bot_removed_too_early",
    "waiting_room_timeout",
    "invalid_meeting_url",
    "meeting_error",
    "MEET_LOGIN_UNAVAILABLE",
    "MEET_LOGIN_REQUIRED",
    "MEET_LOGIN_FAILED_SAML_REJECTED",
    "MEET_LOGIN_FAILED_TIMEOUT",
}


def wait_for_transcription(bot_id: str):
    """Poll GET /bots/{id} jusqu'à ce que la transcription soit prête. MeetingBaaS
    n'envoie pas de webhook dédié à la fin de la transcription."""
    start = time.time()
    while time.time() - start < POLL_TIMEOUT_SECONDS:
        bot_status = get_bot_status(bot_id)
        status_code = bot_status.get("status")
        ready = "prête" if bot_status.get("transcription") else "en attente"
        print(f"[calendar_bots] poll bot {bot_id} -> status={status_code}, transcription={ready}")
        if bot_status.get("transcription"):
            return bot_status
        if bot_status.get("error_code") or status_code in FAILURE_STATUSES:
            raise RuntimeError(f"Le bot a échoué : {bot_status}")
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(f"Transcription indisponible après {POLL_TIMEOUT_SECONDS}s pour le bot {bot_id}")
