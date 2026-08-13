from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from db import Base


class Recap(Base):
    __tablename__ = "recaps"

    recap_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)  # "dictaphone" | "visio" | "calendar"
    created_at = Column(String, nullable=False, default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    transcription = Column(String, nullable=False)
    reporting = Column(JSONB, nullable=False)
    emails = Column(JSONB, nullable=True)  # liste d'emails des participants, récupérée plus tard


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    email = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_code = Column(String, nullable=True)
    verification_code_expires_at = Column(DateTime(timezone=True), nullable=True)
    participants_list_of_recaps = Column(ARRAY(Integer), nullable=False, default=list)
    reset_code = Column(String, nullable=True)
    reset_code_expires_at = Column(DateTime(timezone=True), nullable=True)
