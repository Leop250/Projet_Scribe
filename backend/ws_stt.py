import asyncio
import contextlib
import json
import os
import websockets
from fastapi import WebSocket

REALTIME_PROVIDERS = {
    "deepgram":     "DEEPGRAM_API_KEY",
    "assemblyai":   "ASSEMBLYAI_API_KEY",
    "speechmatics": "SPEECHMATICS_API_KEY",
}


def available_providers() -> list[str]:
    return [p for p, key in REALTIME_PROVIDERS.items() if os.environ.get(key)]


async def transcribe(provider: str, client: WebSocket, sample_rate: int) -> str:
    if provider == "deepgram":
        return await _deepgram(client, sample_rate)
    if provider == "assemblyai":
        return await _assemblyai(client, sample_rate)
    if provider == "speechmatics":
        return await _speechmatics(client, sample_rate)
    raise ValueError(f"Unknown provider: {provider}")


# ─── Deepgram ─────────────────────────────────────────────────────────────────

async def _deepgram(client: WebSocket, sample_rate: int) -> str:
    key = os.environ["DEEPGRAM_API_KEY"]
    url = (
        "wss://api.deepgram.com/v1/listen"
        f"?model=nova-2&language=fr&encoding=linear16"
        f"&sample_rate={sample_rate}&channels=1"
        f"&interim_results=true&punctuate=true&endpointing=300"
    )
    finals: list[str] = []

    async with websockets.connect(url, additional_headers={"Authorization": f"Token {key}"}) as dg_ws:

        async def from_client():
            try:
                while True:
                    msg = await client.receive()
                    if msg["type"] == "websocket.disconnect":
                        break
                    if msg.get("bytes"):
                        await dg_ws.send(msg["bytes"])
                    elif msg.get("text") == "stop":
                        break
            finally:
                with contextlib.suppress(Exception):
                    await dg_ws.send(json.dumps({"type": "CloseStream"}))

        async def from_dg():
            with contextlib.suppress(websockets.ConnectionClosed, Exception):
                async for raw in dg_ws:
                    data = json.loads(raw)
                    if data.get("type") != "Results":
                        continue
                    alt = data["channel"]["alternatives"][0]
                    text = alt.get("transcript", "")
                    is_final = data.get("is_final", False)
                    if text:
                        await client.send_json({"type": "transcript", "text": text, "is_final": is_final})
                        if is_final:
                            finals.append(text)

        await asyncio.gather(from_client(), from_dg())

    return " ".join(finals).strip()


# ─── AssemblyAI ───────────────────────────────────────────────────────────────

async def _assemblyai(client: WebSocket, sample_rate: int) -> str:
    key = os.environ["ASSEMBLYAI_API_KEY"]
    url = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={sample_rate}"
    finals: list[str] = []

    async with websockets.connect(url, additional_headers={"Authorization": key}) as aa_ws:
        # Wait for session start
        with contextlib.suppress(Exception):
            await aa_ws.recv()

        async def from_client():
            try:
                while True:
                    msg = await client.receive()
                    if msg["type"] == "websocket.disconnect":
                        break
                    if msg.get("bytes"):
                        await aa_ws.send(msg["bytes"])
                    elif msg.get("text") == "stop":
                        break
            finally:
                with contextlib.suppress(Exception):
                    await aa_ws.send(json.dumps({"terminate_session": True}))

        async def from_aa():
            with contextlib.suppress(websockets.ConnectionClosed, Exception):
                async for raw in aa_ws:
                    data = json.loads(raw)
                    msg_type = data.get("message_type", "")
                    text = data.get("text", "")
                    if msg_type == "PartialTranscript" and text:
                        await client.send_json({"type": "transcript", "text": text, "is_final": False})
                    elif msg_type == "FinalTranscript" and text:
                        await client.send_json({"type": "transcript", "text": text, "is_final": True})
                        finals.append(text)
                    elif msg_type == "SessionTerminated":
                        break

        await asyncio.gather(from_client(), from_aa())

    return " ".join(finals).strip()


# ─── Speechmatics ─────────────────────────────────────────────────────────────

def _sm_extract_text(results: list) -> str:
    parts = []
    for r in results:
        if r.get("type") == "word":
            parts.append(r.get("content", ""))
        elif r.get("type") == "punctuation" and r.get("attaches_to") == "previous" and parts:
            parts[-1] += r.get("content", "")
    return " ".join(parts).strip()


async def _speechmatics(client: WebSocket, sample_rate: int) -> str:
    key = os.environ["SPEECHMATICS_API_KEY"]
    url = "wss://eu2.rt.speechmatics.com/v2"
    finals: list[str] = []
    seq_no = 0

    async with websockets.connect(url, additional_headers={"Authorization": f"Bearer {key}"}) as sm_ws:
        await sm_ws.send(json.dumps({
            "message": "StartRecognition",
            "audio_format": {"type": "raw", "encoding": "pcm_s16le", "sample_rate": sample_rate},
            "transcription_config": {"language": "fr", "operating_point": "enhanced", "enable_partials": True},
        }))
        with contextlib.suppress(Exception):
            await sm_ws.recv()  # RecognitionStarted

        async def from_client():
            nonlocal seq_no
            try:
                while True:
                    msg = await client.receive()
                    if msg["type"] == "websocket.disconnect":
                        break
                    if msg.get("bytes"):
                        await sm_ws.send(msg["bytes"])
                        seq_no += len(msg["bytes"]) // 2
                    elif msg.get("text") == "stop":
                        break
            finally:
                with contextlib.suppress(Exception):
                    await sm_ws.send(json.dumps({"message": "EndOfStream", "last_seq_no": seq_no}))

        async def from_sm():
            with contextlib.suppress(websockets.ConnectionClosed, Exception):
                async for raw in sm_ws:
                    data = json.loads(raw)
                    msg_type = data.get("message", "")
                    if msg_type == "AddPartialTranscript":
                        text = _sm_extract_text(data.get("results", []))
                        if text:
                            await client.send_json({"type": "transcript", "text": text, "is_final": False})
                    elif msg_type == "AddTranscript":
                        text = _sm_extract_text(data.get("results", []))
                        if text:
                            await client.send_json({"type": "transcript", "text": text, "is_final": True})
                            finals.append(text)
                    elif msg_type == "EndOfTranscript":
                        break

        await asyncio.gather(from_client(), from_sm())

    return " ".join(finals).strip()
