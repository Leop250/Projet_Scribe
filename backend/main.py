import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

load_dotenv()

from ai.classifier import call_classifier  # noqa: E402
from ai.speech_to_text import call_speech_to_text_agent  # noqa: E402
from attendance.models import RecordingSession  # noqa: E402
from attendance.routes import router as attendance_router  # noqa: E402
from auth.dependencies import get_current_user  # noqa: E402
from auth.routes import router as auth_router  # noqa: E402
from auth.users import UserModel, get_by_email  # noqa: E402
from database.database import get_db  # noqa: E402
from database.models import Recap  # noqa: E402

app = FastAPI()


def normalize_url(url: str) -> str:
    if not url:
        return url
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def add_recap_to_user(user: UserModel, recap_id: int) -> None:
    user.participants_list_of_recaps = (user.participants_list_of_recaps or []) + [recap_id]


class RecapSummary(BaseModel):
    id: int
    name: str
    source: str
    created_at: str
    summary: str | None = None
    themes: list[str] = []
    speaker_count: int | None = None


class RecapDetailResponse(BaseModel):
    id: int
    name: str
    source: str
    created_at: str
    summary: str | None = None
    speaker_count: int | None = None
    speakers: list = []
    themes: list[str] = []
    actions: list = []
    transcript: list = []


origins = [normalize_url(os.environ.get("FRONTEND_URL", "http://localhost:5173"))]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Connected."}


@app.post("/recordings")
async def records(
    audio=File(...),
    emails: str = Form(...),
    session_token: str | None = Form(None),
    current_user: UserModel = Depends(get_current_user),
    db_session: Session = Depends(get_db),
):
    temp_path = Path("temp") / audio.filename
    temp_path.parent.mkdir(exist_ok=True)

    with open(temp_path, "wb") as recording_file:
        shutil.copyfileobj(audio.file, recording_file)
    try:
        transcript = call_speech_to_text_agent(temp_path)
        report = call_classifier(transcript)
    finally:
        temp_path.unlink()

    recap = Recap(
        emails=emails,
        name=audio.filename,
        source="dictaphone",
        transcription=transcript,
        reporting=report,
    )

    db_session.add(recap)
    db_session.commit()
    db_session.refresh(recap)

    for email in emails.split(","):
        user = get_by_email(db_session, email)
        if user:
            add_recap_to_user(user, recap.recap_id)

    db_session.commit()

    if session_token:
        session = db_session.query(RecordingSession).filter(RecordingSession.token == session_token).first()
        if session and session.status == "pending":
            session.status = "started"
            session.recap_id = recap.recap_id
            db_session.commit()

    print("Audio received successfully")
    return {
        "status": "ok",
        "id": str(recap.recap_id),
        "Compte-rendu": report,
        "transcription": transcript,
    }


@app.get("/recaps/mine", response_model=list[RecapSummary])
async def list_my_recaps(
    current_user: UserModel = Depends(get_current_user),
    db_session: Session = Depends(get_db),
):
    recap_ids = current_user.participants_list_of_recaps or []
    recaps = (
        db_session.query(Recap).filter(Recap.recap_id.in_(recap_ids)).order_by(Recap.created_at.desc()).all()
    )
    return [
        RecapSummary(
            id=recap.recap_id,
            name=recap.name,
            source=recap.source,
            created_at=recap.created_at,
            summary=(recap.reporting or {}).get("summary"),
            themes=(recap.reporting or {}).get("themes") or [],
            speaker_count=(recap.reporting or {}).get("speaker_count"),
        )
        for recap in recaps
    ]


@app.get("/recaps/{recap_id}", response_model=RecapDetailResponse)
async def get_recap_detail(
    recap_id: int,
    current_user: UserModel = Depends(get_current_user),
    db_session: Session = Depends(get_db),
):
    if recap_id not in (current_user.participants_list_of_recaps or []):
        raise HTTPException(status_code=404, detail="Compte-rendu introuvable.")

    recap = db_session.query(Recap).filter(Recap.recap_id == recap_id).first()
    if recap is None:
        raise HTTPException(status_code=404, detail="Compte-rendu introuvable.")

    reporting = recap.reporting or {}
    return RecapDetailResponse(
        id=recap.recap_id,
        name=recap.name,
        source=recap.source,
        created_at=recap.created_at,
        summary=reporting.get("summary"),
        speaker_count=reporting.get("speaker_count"),
        speakers=reporting.get("speakers") or [],
        themes=reporting.get("themes") or [],
        actions=reporting.get("actions") or [],
        transcript=reporting.get("transcript") or [],
    )


app.include_router(auth_router)
app.include_router(attendance_router)
