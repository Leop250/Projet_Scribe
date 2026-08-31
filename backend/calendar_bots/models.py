from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from database.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CalendarConnection(Base):
    """Connexion calendrier d'un utilisateur (une seule par compte)."""

    __tablename__ = "calendar_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True, index=True)
    meetingbaas_calendar_uuid = Column(String, nullable=False)
    google_calendar_id = Column(String, nullable=False, default="primary")
    google_email = Column(String, nullable=True)
    connected_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CalendarEvent(Base):
    """Événement Google Calendar pour lequel un bot a déjà été programmé (garde-fou
    d'idempotence des webhooks) + emails des participants connus à la programmation."""

    __tablename__ = "calendar_events"

    event_id = Column(String, primary_key=True)
    emails = Column(JSONB, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CalendarBot(Base):
    """Suivi du cycle de vie d'un bot MeetingBaaS (idempotence des webhooks)."""

    __tablename__ = "calendar_bots_state"

    bot_id = Column(String, primary_key=True)
    state = Column(String, nullable=True)  # None -> "processing" -> "saved"
    recording_delay_started = Column(Boolean, nullable=False, default=False, server_default="false")
