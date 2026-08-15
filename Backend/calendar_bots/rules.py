"""Règle métier : un bot rejoint la réunion si son adresse est invitée en tant que participant."""

import os


def should_join(event: dict) -> bool:
    bot_email = os.environ.get("BOT_ATTENDEE_EMAIL", "").lower()
    if not bot_email:
        return False

    attendees = event.get("attendees") or []
    return any((attendee.get("email") or "").lower() == bot_email for attendee in attendees)
