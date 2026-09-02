"""Programmation d'un bot MeetingBaaS pour un événement calendrier, partagée entre le
webhook temps réel et le job de synchronisation périodique."""

from . import client, store

DEFAULT_BOT_NAME = "WhatsON_meeting Notetaker"

RECORDING_DELAY_SECONDS = 3 * 60
RECORDING_DELAY_MINUTES = RECORDING_DELAY_SECONDS // 60

RGPD_ENTRY_MESSAGE = (
    "RGPD : cette réunion est enregistrée par WhatsON_meeting afin d'en générer un compte-rendu. "
    f"Vous disposez de {RECORDING_DELAY_MINUTES} minutes avant le début de l'enregistrement : "
    "si vous ne souhaitez pas être enregistré·e, merci de quitter la réunion avant la fin de ce délai."
)
RECORDING_PAUSE_MESSAGE = (
    f"⏸ Enregistrement en pause pendant {RECORDING_DELAY_MINUTES} minutes pour vous laisser le temps "
    "de rejoindre. Si vous ne souhaitez pas être enregistré·e, c'est le moment de quitter."
)
RECORDING_RESUME_MESSAGE = "L'enregistrement commence maintenant dans la réunion."


def schedule_bot_for_event(calendar_id, event_id, series_id, attendees) -> bool:
    if not event_id or store.is_event_scheduled(event_id):
        return False
    if not store.claim_event(event_id):
        return False
    try:
        client.schedule_bot(
            calendar_id,
            event_id,
            series_id,
            bot_name=DEFAULT_BOT_NAME,
            entry_message=RGPD_ENTRY_MESSAGE,
        )
    except Exception:
        store.unclaim_event(event_id)
        raise
    emails = [a.get("email") for a in (attendees or []) if isinstance(a, dict) and a.get("email")]
    store.save_event_emails(event_id, emails)
    return True
