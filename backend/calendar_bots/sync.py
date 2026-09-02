"""Job de synchronisation périodique : re-scanne les calendriers connectés et programme
les bots manquants, en filet de sécurité des webhooks MeetingBaaS."""

import os
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone

from . import client, rules, store
from .scheduling import schedule_bot_for_event

SYNC_INTERVAL_SECONDS = int(os.environ.get("CALENDAR_SYNC_INTERVAL_SECONDS", "600"))
SYNC_WINDOW_DAYS = 30
INITIAL_DELAY_SECONDS = 30

_started = False


def is_started():
    return _started


def _event_id(event):
    return event.get("event_id") or event.get("id")


def sync_all_calendars():
    report = {"connections": 0, "events_seen": 0, "scheduled": [], "errors": []}
    connections = store.all_connections()
    report["connections"] = len(connections)
    if not connections:
        return report

    now = datetime.now(timezone.utc)
    window_end = (now + timedelta(days=SYNC_WINDOW_DAYS)).isoformat()

    for connection in connections:
        calendar_id = connection["meetingbaas_calendar_uuid"]
        try:
            events = client.list_events(calendar_id, now.isoformat(), window_end)
        except Exception as exc:  # noqa: BLE001
            message = f"list_events a échoué pour {calendar_id} : {exc}"
            print(f"[calendar_bots] sync: {message}")
            report["errors"].append(message)
            continue

        for event in events or []:
            report["events_seen"] += 1
            event_id = _event_id(event)
            try:
                if not event_id or event.get("bot_scheduled") or store.is_event_scheduled(event_id):
                    continue
                detail = client.get_event(calendar_id, event_id)
                if not rules.should_join(detail):
                    continue
                if schedule_bot_for_event(
                    calendar_id, event_id, detail.get("series_id"), detail.get("attendees")
                ):
                    print(f"[calendar_bots] sync: bot programmé pour event {event_id}")
                    report["scheduled"].append(event_id)
            except Exception as exc:  # noqa: BLE001
                message = f"échec de programmation pour {event_id} : {exc}"
                print(f"[calendar_bots] sync: {message}")
                report["errors"].append(message)

    return report


def _loop():
    time.sleep(INITIAL_DELAY_SECONDS)
    while True:
        try:
            sync_all_calendars()
        except Exception:  # noqa: BLE001
            print("[calendar_bots] sync: erreur inattendue\n" + traceback.format_exc())
        time.sleep(SYNC_INTERVAL_SECONDS)


def start_scheduler():
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, name="calendar-sync", daemon=True).start()
    print(f"[calendar_bots] job de synchronisation démarré (toutes les {SYNC_INTERVAL_SECONDS}s)")
