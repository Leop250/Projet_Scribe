import os
import shutil
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

load_dotenv()

from ai.classifier import call_classifier  # noqa: E402
from ai.moderation import NoSpeechDetectedError, verify_report  # noqa: E402
from ai.speech_to_text import call_speech_to_text_agent  # noqa: E402
from auth.dependencies import get_current_user  # noqa: E402
from auth.routes import router as auth_router  # noqa: E402
from auth.users import UserModel, get_by_email  # noqa: E402
from calendar_bots.routes import router as calendar_router  # noqa: E402
from calendar_bots.sync import start_scheduler  # noqa: E402
from database.database import get_db  # noqa: E402
from database.models import Recap  # noqa: E402


class RecapSummary(BaseModel):
    id: int
    name: str
    source: str
    created_at: datetime
    summary: str | None = None
    themes: list[str] = []
    speaker_count: int | None = None


class RecapDetailResponse(BaseModel):
    id: int
    name: str
    source: str
    created_at: datetime
    summary: str | None = None
    speaker_count: int | None = None
    speakers: list = []
    themes: list[str] = []
    actions: list = []
    transcript: list = []


class RecapService:
    """Regroupe la logique métier autour de la création et de la lecture des recaps."""

    @staticmethod
    def normalize_url(url: str) -> str:
        if not url:
            return url
        return url if url.startswith(("http://", "https://")) else f"https://{url}"

    @staticmethod
    def add_recap_to_user(user: UserModel, recap_id: int) -> None:
        current = user.participants_list_of_recaps or []
        if recap_id not in current:
            user.participants_list_of_recaps = current + [recap_id]

    @staticmethod
    def save_audio_to_temp(audio: UploadFile) -> Path:
        safe_name = Path(audio.filename or "upload").name or "upload"
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / f"{uuid4().hex}_{safe_name}"
        with open(temp_path, "wb") as recording_file:
            shutil.copyfileobj(audio.file, recording_file)
        return temp_path

    @staticmethod
    def transcribe_and_classify(temp_path: Path) -> tuple[str, dict]:
        try:
            transcript = call_speech_to_text_agent(temp_path)
            report = call_classifier(transcript)
        finally:
            temp_path.unlink()
        return transcript, report

    @staticmethod
    def create_recap(db_session: Session, emails: str, name: str, transcript: str, report: dict) -> Recap:
        recap = Recap(
            emails=emails,
            name=name,
            source="dictaphone",
            transcription=transcript,
            reporting=report,
        )
        db_session.add(recap)
        db_session.commit()
        db_session.refresh(recap)
        return recap

    @staticmethod
    def attach_participants(db_session: Session, emails: str, recap_id: int) -> None:
        for raw_email in emails.split(","):
            email = raw_email.strip()
            if not email:
                continue
            user = get_by_email(db_session, email)
            if user:
                RecapService.add_recap_to_user(user, recap_id)
        db_session.commit()

    @staticmethod
    def list_summaries(db_session: Session, recap_ids: list[int]) -> list[RecapSummary]:
        recaps = (
            db_session.query(Recap)
            .filter(Recap.recap_id.in_(recap_ids))
            .order_by(Recap.created_at.desc())
            .all()
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

    @staticmethod
    def get_detail(db_session: Session, recap_id: int, current_user: UserModel) -> RecapDetailResponse:
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


recap_service = RecapService()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(lifespan=lifespan)


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS") or os.environ.get("FRONTEND_URL", "http://localhost:5173")
    return [recap_service.normalize_url(origin.strip()) for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Connected."}


@app.post("/recordings")
async def records(
    audio: UploadFile = File(...),
    emails: str = Form(...),
    name: str = Form(..., min_length=1, max_length=200),
    current_user: UserModel = Depends(get_current_user),
    db_session: Session = Depends(get_db),
):
    temp_path = recap_service.save_audio_to_temp(audio)
    try:
        transcript, report = recap_service.transcribe_and_classify(temp_path)
    except NoSpeechDetectedError as error:
        raise HTTPException(status_code=422, detail=str(error))

    report = verify_report(transcript, report)

    recap = recap_service.create_recap(db_session, emails, name, transcript, report)
    recap_service.attach_participants(db_session, emails, recap.recap_id)

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
    return recap_service.list_summaries(db_session, current_user.participants_list_of_recaps or [])


@app.get("/recaps/{recap_id}", response_model=RecapDetailResponse)
async def get_recap_detail(
    recap_id: int,
    current_user: UserModel = Depends(get_current_user),
    db_session: Session = Depends(get_db),
):
    return recap_service.get_detail(db_session, recap_id, current_user)


app.include_router(auth_router)
app.include_router(calendar_router, prefix="/calendar")
