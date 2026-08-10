import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File
from fastapi.middleware.cors import CORSMiddleware

# Les imports ci-dessous doivent rester après load_dotenv() : Auth.config lit
# des variables d'environnement (SECRET_KEY, etc.) au chargement du module.
load_dotenv()

from Auth.dependencies import get_current_user  # noqa: E402
from Auth.routes import router as auth_router  # noqa: E402
from Auth.users import UserModel  # noqa: E402
from classifier import call_classifier  # noqa: E402
from speech_to_text import call_speech_to_text_agent  # noqa: E402

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
async def records(audio=File(...), current_user: UserModel = Depends(get_current_user)):
    temp_path = Path("temp") / audio.filename
    temp_path.parent.mkdir(exist_ok=True)

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)
    try:
        transcript = call_speech_to_text_agent(temp_path)
        report = call_classifier(transcript)
    finally:
        temp_path.unlink()

    print("Audio received successfully")
    return {"status": "ok", "Compte-rendu": report, "transcription": transcript}


app.include_router(auth_router)
