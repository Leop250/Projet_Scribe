from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import JSONB

from db import Base


class Recap(Base):
    __tablename__ = "recaps"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)  # "dictaphone" | "visio"
    created_at = Column(String, nullable=False, default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    transcription = Column(String, nullable=False)
    reporting = Column(JSONB, nullable=False)
