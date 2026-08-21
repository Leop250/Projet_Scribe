import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

load_dotenv()

from Attendance.models import RecordingSession
from Attendance.routes import router as attendance_router
from Auth.dependencies import get_current_user  # noqa: E402
from Auth.routes import router as auth_router  # noqa: E402
from Auth.users import UserModel  # noqa: E402
from classifier import call_classifier  # noqa: E402
from database import get_db  # noqa: E402
from models import Recap  # noqa: E402
from speech_to_text import call_speech_to_text_agent  # noqa: E402

app = FastAPI()


def normalize_url(url: str) -> str:
    if not url:
        return url
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def add_recap_to_user(user: UserModel, recap_id: int) -> None:
    user.participants_list_of_recaps = (user.participants_list_of_recaps or []) + [recap_id]


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
    db: Session = Depends(get_db),
):
    temp_path = Path("temp") / audio.filename
    temp_path.parent.mkdir(exist_ok=True)

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)
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

    db.add(recap)
    db.commit()
    db.refresh(recap)

    for email in emails.split(","):
        user = db.query(UserModel).filter(UserModel.email == email.strip()).first()
        if user:
            add_recap_to_user(user, recap.recap_id)

    db.commit()

    if session_token:
        session = db.query(RecordingSession).filter(RecordingSession.token == session_token).first()
        if session and session.status == "pending":
            session.status = "started"
            db.commit()

    print("Audio received successfully")
    return {
        "status": "ok",
        "id": str(recap.recap_id),
        "Compte-rendu": report,
        "transcription": transcript,
    }


app.include_router(auth_router)
app.include_router(attendance_router)