"""Stockage temporaire (fichier JSON local) — à remplacer par une vraie DB.

Mono-utilisateur pour l'instant : une seule connexion calendrier à la fois,
cohérent avec le reste du backend qui n'a pas encore de notion de compte/session.
"""

import json
from pathlib import Path

STORE_PATH = Path(__file__).parent / "calendar_store.json"

_DEFAULT_STORE_DATA = {"connection": None, "scheduled_events": [], "saved_bots": [], "processing_bots": [], "event_emails": {}}


class CalendarStore:
    def __init__(self, store_path=STORE_PATH):
        self.store_path = store_path

    def _load(self):
        if not self.store_path.exists():
            return dict(_DEFAULT_STORE_DATA)
        with open(self.store_path, "r") as store_file:
            return json.load(store_file)

    def _save(self, store_data):
        with open(self.store_path, "w") as store_file:
            json.dump(store_data, store_file, indent=2)

    def save_connection(self, meetingbaas_calendar_uuid, google_calendar_id):
        store_data = self._load()
        store_data["connection"] = {
            "meetingbaas_calendar_uuid": meetingbaas_calendar_uuid,
            "google_calendar_id": google_calendar_id,
        }
        self._save(store_data)

    def get_connection(self):
        return self._load()["connection"]

    def is_event_scheduled(self, event_id):
        return event_id in self._load()["scheduled_events"]

    def mark_event_scheduled(self, event_id):
        store_data = self._load()
        if event_id not in store_data["scheduled_events"]:
            store_data["scheduled_events"].append(event_id)
            self._save(store_data)

    def is_bot_saved(self, bot_id):
        return bot_id in self._load().get("saved_bots", [])

    def mark_bot_saved(self, bot_id):
        store_data = self._load()
        store_data.setdefault("saved_bots", [])
        if bot_id not in store_data["saved_bots"]:
            store_data["saved_bots"].append(bot_id)
            self._save(store_data)

    def is_bot_processing(self, bot_id):
        return bot_id in self._load().get("processing_bots", [])

    def mark_bot_processing(self, bot_id):
        store_data = self._load()
        store_data.setdefault("processing_bots", [])
        if bot_id not in store_data["processing_bots"]:
            store_data["processing_bots"].append(bot_id)
            self._save(store_data)

    def save_event_emails(self, event_id, emails):
        """Associe les emails des attendees Google Calendar à l'event programmé (connus
        seulement à la programmation, à réutiliser plus tard pour peupler Recap.emails).

        Indexé par event_id et non par bot_id : POST /calendars/{id}/bots ne renvoie
        pas le bot_id créé (seulement l'event_id programmé), donc bot_id est indisponible
        à cet instant. event_id, lui, est aussi présent dans le payload du webhook
        bot.status_change, ce qui permet de refaire le lien une fois la réunion terminée."""
        if not event_id or not emails:
            return
        store_data = self._load()
        store_data.setdefault("event_emails", {})
        store_data["event_emails"][event_id] = emails
        self._save(store_data)

    def get_event_emails(self, event_id):
        return self._load().get("event_emails", {}).get(event_id, [])


_default_calendar_store = CalendarStore()


def save_connection(meetingbaas_calendar_uuid, google_calendar_id):
    return _default_calendar_store.save_connection(meetingbaas_calendar_uuid, google_calendar_id)


def get_connection():
    return _default_calendar_store.get_connection()


def is_event_scheduled(event_id):
    return _default_calendar_store.is_event_scheduled(event_id)


def mark_event_scheduled(event_id):
    return _default_calendar_store.mark_event_scheduled(event_id)


def is_bot_saved(bot_id):
    return _default_calendar_store.is_bot_saved(bot_id)


def mark_bot_saved(bot_id):
    return _default_calendar_store.mark_bot_saved(bot_id)


def is_bot_processing(bot_id):
    return _default_calendar_store.is_bot_processing(bot_id)


def mark_bot_processing(bot_id):
    return _default_calendar_store.mark_bot_processing(bot_id)


def save_event_emails(event_id, emails):
    return _default_calendar_store.save_event_emails(event_id, emails)


def get_event_emails(event_id):
    return _default_calendar_store.get_event_emails(event_id)
