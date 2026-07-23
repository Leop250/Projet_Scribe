"""Règle métier : un bot rejoint la réunion si son adresse est invitée en tant que participant."""

import os


def should_join(event: dict) -> bool:
    bot_email = os.environ.get("BOT_ATTENDEE_EMAIL", "").lower()
    if not bot_email:
        return False

    # Champ "attendees" / "email" non re-vérifié contre une réponse réelle de
    # GET /calendars/:id/events/:event_id (pas encore d'accès API) : à confirmer.
    attendees = event.get("attendees") or []
    return any((a.get("email") or "").lower() == bot_email for a in attendees)
