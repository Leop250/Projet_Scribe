"""Wrapper fin autour de l'API v2 MeetingBaaS (Calendar API)."""

import os

import httpx

BASE_URL = "https://api.meetingbaas.com/v2"


def _headers():
    return {
        "Content-Type": "application/json",
        "x-meeting-baas-api-key": os.environ["MEETING_BAAS_API_KEY"],
    }


def _call(method, path, **kwargs):
    response = httpx.request(method, f"{BASE_URL}{path}", headers=_headers(), timeout=30, **kwargs)
    if not response.is_success:
        raise RuntimeError(f"MeetingBaaS {method} {path} -> {response.status_code}: {response.text}")
    body = response.json()
    # Les réponses MeetingBaaS semblent enveloppées dans {"success": ..., "data": ...}
    # (observé sur GET /calendars) : on déballe si cette forme est présente.
    return body["data"] if isinstance(body, dict) and "data" in body else body


def register_calendar(refresh_token, google_calendar_id="primary"):
    try:
        data = _call("POST", "/calendars", json={
            "calendar_platform": "google",
            "oauth_client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
            "oauth_client_secret": os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            "oauth_refresh_token": refresh_token,
            "raw_calendar_id": google_calendar_id,
        })
    except RuntimeError as exc:
        if "FST_ERR_CALENDAR_CONNECTION_ALREADY_EXISTS" not in str(exc):
            raise
        # Mono-utilisateur pour l'instant (voir store.py) : une seule connexion
        # possible, donc on récupère celle qui existe déjà plutôt que d'échouer.
        data = _call("GET", "/calendars")[0]

    if not isinstance(data, dict) or "calendar_id" not in data:
        raise RuntimeError(f"Réponse MeetingBaaS inattendue (pas de champ 'calendar_id'): {data}")
    return data["calendar_id"]


def get_event(calendar_id, event_id):
    return _call("GET", f"/calendars/{calendar_id}/events/{event_id}")


def schedule_bot(calendar_id, event_id, series_id, bot_name="Scribe Notetaker"):
    return _call("POST", f"/calendars/{calendar_id}/bots", json={
        "event_id": event_id,
        "series_id": series_id,
        "all_occurrences": False,
        "bot_name": bot_name,
        "recording_mode": "speaker_view",
    })
