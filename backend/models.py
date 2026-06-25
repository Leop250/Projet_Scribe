from datetime import datetime
from pydantic import BaseModel


class Combo(BaseModel):
    stt_model: str
    classifier_model: str
    transcript: str
    resume: str
    actions_decisions: list[str]
    taches_assignees: list[str]
    stt_duration_ms: int
    classifier_duration_ms: int
    error: str | None = None


class Recap(BaseModel):
    id: str
    created_at: datetime
    combos: list[Combo]
