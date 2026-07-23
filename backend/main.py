from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from stt import callapi
from llm import generate_report
from db import SessionLocal
from models import Recap

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def normalize_url(url: str) -> str:
    if not url:
        return url
    return url if url.startswith(("http://", "https://")) else f"https://{url}"

origins = [
    normalize_url(os.environ.get("FRONTEND_URL", "http://localhost:5173"))
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Connected."}

@app.post("/recordings")
async def records(audio = File(...), user_id: str = Form(None), db: Session = Depends(get_db)):
    temp_path = Path("temp") / audio.filename
    temp_path.parent.mkdir(exist_ok=True)

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    transcript = callapi(temp_path)
    report = generate_report(transcript)

    temp_path.unlink()

    recap = Recap(
        user_id=user_id,
        name=audio.filename,
        source="dictaphone",
        transcription=transcript,
        reporting=report,
    )
    db.add(recap)
    db.commit()
    db.refresh(recap)

    print("Audio received successfully")

    return {
        "status": "ok",
        "id": str(recap.id),
        "Compte-rendu": report,
        "transcription": transcript,
    }
