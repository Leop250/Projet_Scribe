import asyncio
import io
import time
import os
import httpx
from groq import AsyncGroq

# ─── Provider implementations ─────────────────────────────────────────────────

async def _groq_transcribe(audio_bytes: bytes, model: str) -> dict:
    client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    start = time.monotonic()
    result = await client.audio.transcriptions.create(
        file=("recording.webm", audio_bytes, "audio/webm"),
        model=model,
        language="fr",
        response_format="text",
    )
    return {
        "model": f"groq/{model}",
        "transcript": result,
        "duration_ms": int((time.monotonic() - start) * 1000),
    }


async def _deepgram_transcribe(audio_bytes: bytes) -> dict:
    key = os.environ["DEEPGRAM_API_KEY"]
    start = time.monotonic()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.deepgram.com/v1/listen",
            params={"model": "nova-2", "language": "fr", "punctuate": "true", "diarize": "false"},
            headers={"Authorization": f"Token {key}", "Content-Type": "audio/webm"},
            content=audio_bytes,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
    transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
    return {
        "model": "deepgram/nova-2",
        "transcript": transcript,
        "duration_ms": int((time.monotonic() - start) * 1000),
    }


async def _assemblyai_transcribe(audio_bytes: bytes) -> dict:
    key = os.environ["ASSEMBLYAI_API_KEY"]
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=120) as client:
        # Upload
        up = await client.post(
            "https://api.assemblyai.com/v2/upload",
            headers={"authorization": key},
            content=audio_bytes,
        )
        up.raise_for_status()
        upload_url = up.json()["upload_url"]

        # Request transcript
        req = await client.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={"authorization": key},
            json={"audio_url": upload_url, "language_code": "fr"},
        )
        req.raise_for_status()
        transcript_id = req.json()["id"]

        # Poll until complete
        while True:
            poll = await client.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers={"authorization": key},
            )
            poll.raise_for_status()
            status = poll.json()["status"]
            if status == "completed":
                transcript = poll.json()["text"]
                break
            if status == "error":
                raise RuntimeError(f"AssemblyAI error: {poll.json().get('error')}")
            await asyncio.sleep(2)

    return {
        "model": "assemblyai/best",
        "transcript": transcript,
        "duration_ms": int((time.monotonic() - start) * 1000),
    }


async def _speechmatics_transcribe(audio_bytes: bytes) -> dict:
    key = os.environ["SPEECHMATICS_API_KEY"]
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=120) as client:
        # Submit job
        resp = await client.post(
            "https://asr.api.speechmatics.com/v2/jobs/",
            headers={"Authorization": f"Bearer {key}"},
            files={"data_file": ("recording.webm", io.BytesIO(audio_bytes), "audio/webm")},
            data={"config": '{"type":"transcription","transcription_config":{"language":"fr"}}'},
        )
        resp.raise_for_status()
        job_id = resp.json()["id"]

        # Poll until complete
        while True:
            poll = await client.get(
                f"https://asr.api.speechmatics.com/v2/jobs/{job_id}",
                headers={"Authorization": f"Bearer {key}"},
            )
            poll.raise_for_status()
            job_status = poll.json()["job"]["status"]
            if job_status == "done":
                break
            if job_status in ("rejected", "deleted"):
                raise RuntimeError(f"Speechmatics job {job_status}")
            await asyncio.sleep(2)

        # Fetch transcript
        txt = await client.get(
            f"https://asr.api.speechmatics.com/v2/jobs/{job_id}/transcript?format=txt",
            headers={"Authorization": f"Bearer {key}"},
        )
        txt.raise_for_status()
        transcript = txt.text.strip()

    return {
        "model": "speechmatics/enhanced",
        "transcript": transcript,
        "duration_ms": int((time.monotonic() - start) * 1000),
    }


async def _openai_whisper_transcribe(audio_bytes: bytes) -> dict:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    start = time.monotonic()
    result = await client.audio.transcriptions.create(
        file=("recording.webm", audio_bytes, "audio/webm"),
        model="whisper-1",
        language="fr",
    )
    return {
        "model": "openai/whisper-1",
        "transcript": result.text,
        "duration_ms": int((time.monotonic() - start) * 1000),
    }


# ─── Provider registry ────────────────────────────────────────────────────────

# Each entry: (env_var_required, coroutine_factory)
_PROVIDERS: list[tuple[str, callable]] = [
    ("GROQ_API_KEY",        lambda b: _groq_transcribe(b, "whisper-large-v3")),
    ("GROQ_API_KEY",        lambda b: _groq_transcribe(b, "whisper-large-v3-turbo")),
    ("DEEPGRAM_API_KEY",    lambda b: _deepgram_transcribe(b)),
    ("ASSEMBLYAI_API_KEY",  lambda b: _assemblyai_transcribe(b)),
    ("SPEECHMATICS_API_KEY",lambda b: _speechmatics_transcribe(b)),
    ("OPENAI_API_KEY",      lambda b: _openai_whisper_transcribe(b)),
]


async def run_all_stt(audio_bytes: bytes) -> list[dict]:
    active = [
        factory(audio_bytes)
        for env_var, factory in _PROVIDERS
        if os.environ.get(env_var)
    ]
    results = await asyncio.gather(*active, return_exceptions=True)
    ok = [r for r in results if not isinstance(r, Exception)]
    errors = [r for r in results if isinstance(r, Exception)]
    for e in errors:
        print(f"[STT error] {e}")
    return ok
