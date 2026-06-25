import asyncio
import contextlib
import uuid
from datetime import datetime, UTC

from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import Combo, Recap
import stt
import classifier
import storage
import visio

app = FastAPI(title="Scribe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Providers info ───────────────────────────────────────────────────────────

@app.get("/providers")
async def list_providers():
    return {
        "visio": bool(os.environ.get("VEXA_API_KEY")),
        "dictaphone_stt": [
            label
            for env_var, label in [
                ("GROQ_API_KEY",         "groq/whisper-large-v3"),
                ("GROQ_API_KEY",         "groq/whisper-large-v3-turbo"),
                ("DEEPGRAM_API_KEY",     "deepgram/nova-2"),
                ("ASSEMBLYAI_API_KEY",   "assemblyai/best"),
                ("SPEECHMATICS_API_KEY", "speechmatics/enhanced"),
                ("OPENAI_API_KEY",       "openai/whisper-1"),
            ]
            if os.environ.get(env_var)
        ],
    }


# ─── Dictaphone ───────────────────────────────────────────────────────────────

@app.post("/recordings", response_model=Recap)
async def upload_recording(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    stt_results = await stt.run_all_stt(audio_bytes)
    if not stt_results:
        raise HTTPException(status_code=502, detail="All STT models failed")

    all_tasks = [
        (stt_result, clf_model)
        for stt_result in stt_results
        for clf_model in classifier.CLASSIFIER_MODELS
    ]

    classify_futures = await asyncio.gather(
        *[classifier._classify_one(t[0]["transcript"], t[1]) for t in all_tasks],
        return_exceptions=True,
    )

    combos: list[Combo] = []
    for (stt_result, _), clf_result in zip(all_tasks, classify_futures):
        if isinstance(clf_result, Exception):
            continue
        combos.append(Combo(
            stt_model=stt_result["model"],
            classifier_model=clf_result["model"],
            transcript=stt_result["transcript"],
            resume=clf_result["resume"],
            actions_decisions=clf_result["actions_decisions"],
            taches_assignees=clf_result["taches_assignees"],
            stt_duration_ms=stt_result["duration_ms"],
            classifier_duration_ms=clf_result["duration_ms"],
        ))

    recap = Recap(id=str(uuid.uuid4()), created_at=datetime.now(UTC), combos=combos)
    storage.save(recap)
    return recap


@app.get("/recaps/{recap_id}", response_model=Recap)
async def get_recap(recap_id: str):
    recap = storage.get(recap_id)
    if not recap:
        raise HTTPException(status_code=404, detail="Recap not found")
    return recap


# ─── Visio (Vexa) ─────────────────────────────────────────────────────────────

VISIO_PROVIDERS = [
    {"id": "vexa", "label": "Vexa", "env": "VEXA_API_KEY"},
]


@app.get("/visio/providers")
async def list_visio_providers():
    return [p for p in VISIO_PROVIDERS if os.environ.get(p["env"])]


class VisioStartBody(BaseModel):
    meeting_url: str
    provider: str = "vexa"


@app.post("/visio/start")
async def visio_start(body: VisioStartBody):
    known = {p["id"]: p for p in VISIO_PROVIDERS}
    if body.provider not in known:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {body.provider}")
    if not os.environ.get(known[body.provider]["env"]):
        raise HTTPException(status_code=503, detail=f"{body.provider} API key not configured")
    try:
        result = await visio.start_bot(body.meeting_url, provider=body.provider)
        return {**result, "provider": body.provider}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"{body.provider} error: {e}")


@app.websocket("/ws/visio/{native_meeting_id}")
async def ws_visio(websocket: WebSocket, native_meeting_id: str, provider: str = "vexa"):
    await websocket.accept()
    stopped_by_user = False
    meeting_ended   = False
    session_complete = False
    try:
        await websocket.send_json({"type": "status", "message": "Bot en train de rejoindre la réunion…"})

        transcript, stopped_by_user, meeting_ended = await visio.stream_transcript(websocket, native_meeting_id, provider=provider)

        if not transcript.strip():
            if meeting_ended:
                await websocket.send_json({"type": "session_expired"})
            else:
                await websocket.send_json({"type": "cancelled"})
            return

        await websocket.send_json({"type": "classifying"})

        clf_results = await classifier.run_all_classifiers(transcript)

        combos = [
            Combo(
                stt_model="vexa/google_meet",
                classifier_model=clf["model"],
                transcript=transcript,
                resume=clf["resume"],
                actions_decisions=clf["actions_decisions"],
                taches_assignees=clf["taches_assignees"],
                stt_duration_ms=0,
                classifier_duration_ms=clf["duration_ms"],
            )
            for clf in clf_results
        ]

        recap = Recap(id=str(uuid.uuid4()), created_at=datetime.now(UTC), combos=combos)
        storage.save(recap)

        await websocket.send_json({"type": "recap", "data": recap.model_dump(mode="json")})
        session_complete = True

    except Exception as e:
        with contextlib.suppress(Exception):
            await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        # Stop the bot when the session ended intentionally:
        # - user clicked "Arrêter"
        # - recap was generated
        # - meeting ended naturally (Vexa sent "done")
        # On a plain connection drop we leave the bot running so the user can reconnect.
        if session_complete or stopped_by_user or meeting_ended:
            with contextlib.suppress(Exception):
                await visio.stop_bot(native_meeting_id, provider=provider)
        with contextlib.suppress(Exception):
            await websocket.close()
