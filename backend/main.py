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
from Auth.dependencies import get_current_user  
from Auth.routes import router as auth_router  
from Auth.users import UserModel  
from classifier import call_classifier 
from database import get_db
from speech_to_text import call_speech_to_text_agent 

app = FastAPI()


def normalize_url(url: str) -> str:
    if not url:
        return url
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


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


@app.post("/recap")
async def recap(current_user: UserModel = Depends(get_current_user)):
    return {"message": "Audio received, not yet able to transcript it"}


@app.post("/recordings")
async def records(
    audio=File(...), 
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

    if session_token:
        session = db.query(RecordingSession).filter(RecordingSession.token == session_token).first()
        if session and session.status == "pending":
            session.status = "started"
            db.commit()

    print("Audio received successfully")
    return {"status": "ok", "Compte-rendu": report, "transcription": transcript}


app.include_router(auth_router)
app.include_router(attendance_router)