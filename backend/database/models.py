from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from database.database import Base


class Recap(Base):
    __tablename__ = "recaps"

    recap_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)  # "dictaphone" | "visio" | "calendar"
    created_at = Column(
        String, nullable=False, default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    transcription = Column(String, nullable=False)
    reporting = Column(JSONB, nullable=False)
    emails = Column(String, nullable=False)
