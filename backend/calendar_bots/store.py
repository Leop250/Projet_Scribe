"""État de l'intégration calendrier, persisté en base (remplace l'ancien store JSON).

- la connexion calendrier est liée à un utilisateur (1 par compte) ;
- les tables d'événements / bots servent de garde-fous d'idempotence pour les
  webhooks MeetingBaaS (qui n'ont pas de contexte utilisateur).
"""

from contextlib import contextmanager

from database.database import SessionLocal

from .models import CalendarBot, CalendarConnection, CalendarEvent


@contextmanager
def _session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def save_connection(user_id, meetingbaas_calendar_uuid, google_calendar_id="primary", google_email=None):
    with _session() as session:
        connection = session.query(CalendarConnection).filter_by(user_id=user_id).first()
        if connection is None:
            connection = CalendarConnection(user_id=user_id)
            session.add(connection)
        connection.meetingbaas_calendar_uuid = meetingbaas_calendar_uuid
        connection.google_calendar_id = google_calendar_id
        if google_email is not None:
            connection.google_email = google_email


def get_connection(user_id):
    with _session() as session:
        connection = session.query(CalendarConnection).filter_by(user_id=user_id).first()
        if connection is None:
            return None
        return {
            "meetingbaas_calendar_uuid": connection.meetingbaas_calendar_uuid,
            "google_calendar_id": connection.google_calendar_id,
            "google_email": connection.google_email,
            "connected_at": connection.connected_at,
        }


def get_connection_by_calendar_uuid(meetingbaas_calendar_uuid):
    with _session() as session:
        connection = (
            session.query(CalendarConnection)
            .filter_by(meetingbaas_calendar_uuid=meetingbaas_calendar_uuid)
            .first()
        )
        if connection is None:
            return None
        return {"user_id": connection.user_id, "google_calendar_id": connection.google_calendar_id}


def delete_connection(user_id):
    with _session() as session:
        connection = session.query(CalendarConnection).filter_by(user_id=user_id).first()
        if connection is None:
            return None
        calendar_uuid = connection.meetingbaas_calendar_uuid
        session.delete(connection)
        return calendar_uuid


def is_event_scheduled(event_id):
    with _session() as session:
        return session.get(CalendarEvent, event_id) is not None


def mark_event_scheduled(event_id):
    with _session() as session:
        if session.get(CalendarEvent, event_id) is None:
            session.add(CalendarEvent(event_id=event_id))


def save_event_emails(event_id, emails):
    if not event_id or not emails:
        return
    with _session() as session:
        event = session.get(CalendarEvent, event_id)
        if event is None:
            event = CalendarEvent(event_id=event_id)
            session.add(event)
        event.emails = emails


def get_event_emails(event_id):
    if not event_id:
        return []
    with _session() as session:
        event = session.get(CalendarEvent, event_id)
        return (event.emails if event else None) or []


def _get_or_create_bot(session, bot_id):
    bot = session.get(CalendarBot, bot_id)
    if bot is None:
        bot = CalendarBot(bot_id=bot_id)
        session.add(bot)
    return bot


def is_bot_saved(bot_id):
    with _session() as session:
        bot = session.get(CalendarBot, bot_id)
        return bool(bot and bot.state == "saved")


def mark_bot_saved(bot_id):
    with _session() as session:
        _get_or_create_bot(session, bot_id).state = "saved"


def is_bot_processing(bot_id):
    with _session() as session:
        bot = session.get(CalendarBot, bot_id)
        return bool(bot and bot.state == "processing")


def mark_bot_processing(bot_id):
    with _session() as session:
        bot = _get_or_create_bot(session, bot_id)
        if bot.state != "saved":
            bot.state = "processing"


def clear_bot_processing(bot_id):
    with _session() as session:
        bot = session.get(CalendarBot, bot_id)
        if bot is not None and bot.state == "processing":
            bot.state = None


def is_recording_delay_started(bot_id):
    with _session() as session:
        bot = session.get(CalendarBot, bot_id)
        return bool(bot and bot.recording_delay_started)


def mark_recording_delay_started(bot_id):
    with _session() as session:
        _get_or_create_bot(session, bot_id).recording_delay_started = True
