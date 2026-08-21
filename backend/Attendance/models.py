from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from database import Base


class RecordingSession(Base):
    __tablename__ = "recording_sessions"

    id = Column("session_id", Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    organizer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    headcount = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")  # "pending" | "started"
    recap_id = Column(Integer, ForeignKey("recaps.recap_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Signature(Base):
    __tablename__ = "attendance_signatures"

    id = Column("signature_id", Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("recording_sessions.session_id"), nullable=False, index=True)
    nom = Column(String, nullable=False)
    image_data = Column(String, nullable=False)
    signed_at = Column(DateTime(timezone=True), server_default=func.now())
