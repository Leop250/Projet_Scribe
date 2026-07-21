from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from stt import callapi
from llm import generate_report

app = FastAPI()

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
    return {"message" : "Connected."}

@app.post("/recap")
async def recap():
    return {"message" : "Audio received, not yet able to transcript it"}

@app.post("/recordings")
async def records(audio = File(...)):
    temp_path = Path("temp") / audio.filename
    temp_path.parent.mkdir(exist_ok=True)

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    transcript = callapi(temp_path)
    print(transcript)    
    report = generate_report(transcript)

    temp_path.unlink()

    print("Audio received successfully")
    return {
    "status": "ok",
    "Compte-rendu": report,
    "transcription": transcript
}