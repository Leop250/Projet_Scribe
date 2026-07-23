import os

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from config import get_meeting_baas_api_key
from meetingbaas_client import (
    DEFAULT_BOT_NAME,
    DEFAULT_RECORDING_MODE,
    create_bot,
    get_bot_status,
    list_bots_history,
    remove_bot,
    wait_for_completion,
)
from save_meeting import save_meeting

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


class BotRequest(BaseModel):
    meeting_url: str
    bot_name: str = DEFAULT_BOT_NAME
    provider: str | None = None
    recording_mode: str = DEFAULT_RECORDING_MODE


def run_meeting_bot(meeting_url: str, bot_name: str, provider: str | None, recording_mode: str) -> None:
    api_key = get_meeting_baas_api_key()
    bot_id = create_bot(
        api_key,
        meeting_url,
        bot_name,
        transcription_enabled=True,
        provider=provider,
        recording_mode=recording_mode,
    )
    try:
        result = wait_for_completion(api_key, bot_id)
        saved = save_meeting(result, bot_name=bot_name)
        print(f"[OK] Recap enregistré en base (id={saved['id']}).")
    except Exception as exc:
        print(f"[ERREUR] Échec du traitement de la réunion {meeting_url} : {exc}")
        remove_bot(api_key, bot_id)


@app.get("/")
async def root():
    return {"message": "Connected."}


@app.post("/bots")
async def send_bot(payload: BotRequest, background_tasks: BackgroundTasks):
    """Envoie le bot Scribe dans la réunion Teams/Meet ; le recap est enregistré
    en base une fois la réunion terminée (traitement en tâche de fond)."""
    background_tasks.add_task(
        run_meeting_bot,
        payload.meeting_url,
        payload.bot_name,
        payload.provider,
        payload.recording_mode,
    )
    return {"status": "ok", "message": "Bot envoyé, le recap sera enregistré à la fin de la réunion."}


@app.get("/bots/{bot_id}")
async def bot_status(bot_id: str):
    try:
        api_key = get_meeting_baas_api_key()
        return get_bot_status(api_key, bot_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/bots")
async def bots_history(limit: int = 20):
    api_key = get_meeting_baas_api_key()
    return list_bots_history(api_key, limit=limit)


@app.delete("/bots/{bot_id}")
async def delete_bot(bot_id: str):
    api_key = get_meeting_baas_api_key()
    remove_bot(api_key, bot_id)
    return {"status": "ok"}
