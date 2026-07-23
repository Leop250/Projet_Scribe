import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB

from db import Base


class Recap(Base):
    __tablename__ = "recaps"

    recap_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)  # "dictaphone" | "meeting_bot"
    created_at = Column(String, nullable=False, default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    transcription = Column(String, nullable=False)
    reporting = Column(JSONB, nullable=False)
    emails = Column(String, nullable = False)

class User(Base):
    __tablename__ = "users"

    email_id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    participants_list_of_recaps = Column(String, defaut=False)