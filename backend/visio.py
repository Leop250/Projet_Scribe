import asyncio
import contextlib
import json
import os
import re
import httpx
import websockets
from fastapi import WebSocket

VEXA_BASE = "https://api.cloud.vexa.ai"
VEXA_WS   = "wss://api.cloud.vexa.ai/ws"
BOT_JOIN_WARN_SECS = 60


def _extract_meet_id(url: str) -> str:
    match = re.search(r'meet\.google\.com/([a-z]{3}-[a-z]{4}-[a-z]{3})', url)
    if not match:
        raise ValueError(f"URL Google Meet invalide : {url}")
    return match.group(1)


async def start_bot(meeting_url: str, provider: str = "vexa") -> dict:
    key = os.environ["VEXA_API_KEY"]
    native_id = _extract_meet_id(meeting_url)

    print(f"[Vexa] start_bot → POST /bots for {native_id}")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{VEXA_BASE}/bots",
                headers={"X-API-Key": key, "Content-Type": "application/json"},
                json={"platform": "google_meet", "native_meeting_id": native_id},
            )
        print(f"[Vexa] start_bot ← {resp.status_code}: {resp.text[:200]}")
        if resp.status_code == 409:
            print(f"[Vexa] Bot already in meeting {native_id}, proceeding")
        else:
            resp.raise_for_status()
    except httpx.HTTPStatusError:
        raise
    except Exception as e:
        print(f"[Vexa] start_bot network error: {type(e).__name__}: {e}")
        raise

    return {"native_meeting_id": native_id, "platform": "google_meet"}


async def stop_bot(native_meeting_id: str, provider: str = "vexa") -> None:
    key = os.environ["VEXA_API_KEY"]
    async with httpx.AsyncClient(timeout=10) as client:
        with contextlib.suppress(Exception):
            await client.delete(
                f"{VEXA_BASE}/bots/google_meet/{native_meeting_id}",
                headers={"X-API-Key": key},
            )


async def stream_transcript(client_ws: WebSocket, native_meeting_id: str, provider: str = "vexa") -> tuple[str, bool, bool]:
    """Returns (transcript, stopped_by_user, meeting_ended)."""
    key = os.environ["VEXA_API_KEY"]

    stop_event      = asyncio.Event()
    stopped_by_user = [False]
    bot_in_meeting  = [False]
    meeting_ended   = [False]
    segments: dict[str, dict] = {}       # all segments for real-time display
    confirmed_segs: dict[str, dict] = {} # only confirmed, used for final transcript
    sent_text: dict[str, str] = {}

    async def listen_for_stop():
        try:
            while not stop_event.is_set():
                try:
                    msg = await asyncio.wait_for(client_ws.receive(), timeout=2)
                except asyncio.TimeoutError:
                    continue
                if msg.get("text") == "stop":
                    # Explicit stop from the user — mark it so stop_bot() is called
                    stopped_by_user[0] = True
                    break
                if msg.get("type") == "websocket.disconnect":
                    # Plain connection drop — do NOT mark as stopped_by_user
                    # so the bot stays in the meeting for reconnection
                    break
        except Exception as e:
            print(f"[WS listen] {e}")
        finally:
            stop_event.set()

    async def listen_vexa():
        warned  = False
        elapsed = [0]

        async def _warn_loop():
            nonlocal warned
            while not stop_event.is_set():
                await asyncio.sleep(2)
                elapsed[0] += 2
                if not warned and not bot_in_meeting[0] and not segments and elapsed[0] >= BOT_JOIN_WARN_SECS:
                    warned = True
                    with contextlib.suppress(Exception):
                        await client_ws.send_json({
                            "type": "warning",
                            "message": "Le bot est peut-être en salle d'attente — admettez-le depuis Google Meet.",
                        })

        warn_task = asyncio.create_task(_warn_loop())
        reconnect_attempts = 0
        max_reconnects     = 5

        try:
            while not stop_event.is_set():
                try:
                    async with websockets.connect(
                        VEXA_WS,
                        additional_headers={"X-API-Key": key},
                    ) as vexa_ws:
                        if stop_event.is_set():
                            break
                        reconnect_attempts = 0
                        sent_text.clear()
                        confirmed_segs.clear()

                        await vexa_ws.send(json.dumps({
                            "action": "subscribe",
                            "meetings": [{"platform": "google_meet", "native_id": native_meeting_id}],
                        }))
                        print(f"[Vexa WS] Subscribed to {native_meeting_id}")

                        while not stop_event.is_set():
                            try:
                                raw = await asyncio.wait_for(vexa_ws.recv(), timeout=5)
                            except asyncio.TimeoutError:
                                continue

                            try:
                                msg = json.loads(raw)
                            except Exception:
                                continue

                            msg_type = msg.get("type")
                            print(f"[Vexa WS] {msg_type}: {json.dumps(msg)[:800]}")

                            if msg_type == "subscribed":
                                subscribed_meetings = msg.get("meetings", [])
                                if not subscribed_meetings:
                                    print(f"[Vexa WS] Subscribed with empty meetings — stale session, cleaning up")
                                    meeting_ended[0] = True
                                    stop_event.set()
                                    break
                                else:
                                    bot_in_meeting[0] = True
                                    print(f"[Vexa WS] Subscribed OK — bot confirmed in meeting")

                            elif msg_type == "meeting.status":
                                payload = msg.get("payload") or msg
                                status  = payload.get("status", "")
                                print(f"[Vexa WS] Meeting status: {status!r}")

                                if status == "in_meeting":
                                    bot_in_meeting[0] = True
                                elif status == "done":
                                    meeting_ended[0] = True
                                    with contextlib.suppress(Exception):
                                        await client_ws.send_json({"type": "bot_status", "status": status})
                                    stop_event.set()
                                    break

                                with contextlib.suppress(Exception):
                                    await client_ws.send_json({"type": "bot_status", "status": status})

                            elif msg_type in ("transcript", "transcript.mutable"):
                                top_speaker = msg.get("speaker", "")

                                # pending  = live in-progress (low latency, may have smaller chunks)
                                # confirmed = finalized (Vexa may merge several pending into one)
                                # Use start time as uid so confirmed replaces pending in-place.
                                for field in ("pending", "confirmed"):
                                    for seg in msg.get(field, []):
                                        start   = seg.get("start", 0)
                                        text    = seg.get("text", "").strip()
                                        speaker = seg.get("speaker", "") or top_speaker
                                        uid     = f"{start:.3f}"

                                        segments[uid] = {"text": text, "speaker": speaker, "start": start}
                                        if field == "confirmed":
                                            confirmed_segs[uid] = segments[uid]
                                        if text and sent_text.get(uid) != text:
                                            sent_text[uid] = text
                                            with contextlib.suppress(Exception):
                                                await client_ws.send_json({
                                                    "type": "transcript",
                                                    "uid": uid,
                                                    "speaker": speaker,
                                                    "text": text,
                                                })

                                # Legacy format fallback (transcript.mutable with payload.segments)
                                payload = msg.get("payload") or {}
                                for i, seg in enumerate(payload.get("segments", [])):
                                    uid     = seg.get("session_uid") or f"seg_{i}"
                                    text    = seg.get("text", "").strip()
                                    speaker = seg.get("speaker", "")
                                    start   = seg.get("absolute_start_time", i)

                                    segments[uid] = {"text": text, "speaker": speaker, "start": start}
                                    if text and sent_text.get(uid) != text:
                                        sent_text[uid] = text
                                        with contextlib.suppress(Exception):
                                            await client_ws.send_json({
                                                "type": "transcript",
                                                "uid": uid,
                                                "speaker": speaker,
                                                "text": text,
                                            })

                            elif msg_type == "error":
                                print(f"[Vexa WS] Error from Vexa: {msg}")
                                stale_errors = {"invalid_subscribe_payload", "authorization_call_failed"}
                                if msg.get("error") in stale_errors:
                                    print(f"[Vexa WS] Stale session ({msg.get('error')}) — will clean up")
                                    meeting_ended[0] = True
                                    stop_event.set()
                                    break

                            else:
                                print(f"[Vexa WS] Unknown type: {msg_type}")

                except websockets.ConnectionClosed as e:
                    if stop_event.is_set():
                        break
                    reconnect_attempts += 1
                    if reconnect_attempts > max_reconnects:
                        print(f"[Vexa WS] Too many disconnects, giving up")
                        with contextlib.suppress(Exception):
                            await client_ws.send_json({"type": "error", "message": "Connexion Vexa perdue."})
                        break
                    print(f"[Vexa WS] Disconnected ({e}), reconnect {reconnect_attempts}/{max_reconnects}…")
                    await asyncio.sleep(2)

                except Exception as e:
                    print(f"[Vexa WS] Unexpected error: {e}")
                    with contextlib.suppress(Exception):
                        await client_ws.send_json({"type": "error", "message": f"Erreur Vexa : {e}"})
                    break

        finally:
            warn_task.cancel()
            stop_event.set()

    await asyncio.gather(listen_for_stop(), listen_vexa())

    # Prefer confirmed segments for the transcript (no duplicates from pending chunks).
    # Fall back to all segments if no confirmed arrived (e.g. session stopped mid-utterance).
    final = confirmed_segs if confirmed_segs else segments
    sorted_segs = sorted(final.values(), key=lambda s: s.get("start", 0))
    parts = [
        f"{s['speaker']}: {s['text']}" if s["speaker"] else s["text"]
        for s in sorted_segs
        if s["text"]
    ]
    return "\n".join(parts), stopped_by_user[0], meeting_ended[0]
