"""Stockage temporaire (fichier JSON local) — à remplacer par une vraie DB.

Mono-utilisateur pour l'instant : une seule connexion calendrier à la fois,
cohérent avec le reste du backend qui n'a pas encore de notion de compte/session.
"""

import json
from pathlib import Path

STORE_PATH = Path(__file__).parent / "calendar_store.json"

_DEFAULT = {"connection": None, "scheduled_events": [], "saved_bots": [], "processing_bots": []}


def _load():
    if not STORE_PATH.exists():
        return dict(_DEFAULT)
    with open(STORE_PATH, "r") as f:
        return json.load(f)


def _save(data):
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def save_connection(meetingbaas_calendar_uuid, google_calendar_id):
    data = _load()
    data["connection"] = {
        "meetingbaas_calendar_uuid": meetingbaas_calendar_uuid,
        "google_calendar_id": google_calendar_id,
    }
    _save(data)


def get_connection():
    return _load()["connection"]


def is_event_scheduled(event_id):
    return event_id in _load()["scheduled_events"]


def mark_event_scheduled(event_id):
    data = _load()
    if event_id not in data["scheduled_events"]:
        data["scheduled_events"].append(event_id)
        _save(data)


def is_bot_saved(bot_id):
    return bot_id in _load().get("saved_bots", [])


def mark_bot_saved(bot_id):
    data = _load()
    data.setdefault("saved_bots", [])
    if bot_id not in data["saved_bots"]:
        data["saved_bots"].append(bot_id)
        _save(data)


def is_bot_processing(bot_id):
    return bot_id in _load().get("processing_bots", [])


def mark_bot_processing(bot_id):
    data = _load()
    data.setdefault("processing_bots", [])
    if bot_id not in data["processing_bots"]:
        data["processing_bots"].append(bot_id)
        _save(data)
