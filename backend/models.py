import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from db import Base


class Recap(Base):
    __tablename__ = "recaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)  # "dictaphone" | "meeting_bot"
    created_at = Column(String, nullable=False, default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    transcription = Column(String, nullable=False)
    reporting = Column(JSONB, nullable=False)
