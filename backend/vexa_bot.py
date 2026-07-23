#!/usr/bin/env python3
import re
import sys
import time
import requests

from config import get_vexa_api_key

API_BASE = "https://api.cloud.vexa.ai"
BOT_NAME = "Scribe"
POLL_INTERVAL_SECONDS = 15
POLL_TIMEOUT_SECONDS = 60 * 60


def parse_meeting(raw: str) -> dict:
    """Détecte la plateforme et extrait les infos nécessaires à partir
    d'un lien (Google Meet) ou d'un texte d'invitation (Teams)."""

    # Google Meet : https://meet.google.com/abc-defg-hij
    m = re.search(r"meet\.google\.com/([a-z]{3}-[a-z]{4}-[a-z]{3})", raw, re.IGNORECASE)
    if m:
        return {"platform": "google_meet", "native_meeting_id": m.group(1), "passcode": None}

    # Teams : besoin du "Conference ID" (numérique) + "Passcode"
    conf_id = re.search(r"Conference ID:?\s*([\d\s]{6,})#?", raw, re.IGNORECASE)
    passcode = re.search(r"Passcode:?\s*([^\s]+)", raw, re.IGNORECASE)
    if conf_id:
        native_id = re.sub(r"\s", "", conf_id.group(1))
        return {
            "platform": "teams",
            "native_meeting_id": native_id,
            "passcode": passcode.group(1) if passcode else None,
        }

    raise ValueError(
        "Impossible de reconnaître ce lien. Colle soit un lien meet.google.com, "
        "soit le texte complet de l'invitation Teams (avec Conference ID et Passcode)."
    )


def create_bot(api_key: str, meeting: dict) -> dict:
    url = f"{API_BASE}/bots"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    payload = {
        "platform": meeting["platform"],
        "native_meeting_id": meeting["native_meeting_id"],
        "bot_name": BOT_NAME,
        "recording_enabled": True,
        "transcribe_enabled": True,
        "transcription_tier": "realtime",
    }
    if meeting["platform"] == "teams":
        if not meeting["passcode"]:
            raise ValueError("Passcode Teams introuvable dans le texte fourni.")
        payload["passcode"] = meeting["passcode"]

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    print(f"[OK] {BOT_NAME} envoyé dans la réunion {meeting['platform']}/{meeting['native_meeting_id']}.")
    return response.json()


def get_transcript(api_key: str, platform: str, native_meeting_id: str) -> dict:
    url = f"{API_BASE}/transcripts/{platform}/{native_meeting_id}"
    headers = {"X-API-Key": api_key}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def poll_transcript(api_key: str, platform: str, native_meeting_id: str) -> dict:
    start = time.time()
    while time.time() - start < POLL_TIMEOUT_SECONDS:
        data = get_transcript(api_key, platform, native_meeting_id)
        segments = data.get("data", data).get("transcripts") or data.get("segments") or []
        if segments:
            return data
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError("Aucun segment de transcript reçu avant le délai imparti.")


def main():
    raw_input_str = input("Lien (Google Meet ou Teams) : ").strip()
    if not raw_input_str:
        sys.exit("Aucun lien fourni.")

    try:
        api_key = get_vexa_api_key()
        meeting = parse_meeting(raw_input_str)
        create_bot(api_key, meeting)
        result = poll_transcript(api_key, meeting["platform"], meeting["native_meeting_id"])

        print("\n=== Transcript ===")
        segments = result.get("data", result).get("transcripts") or result.get("segments") or []
        for seg in segments:
            print(f"[{seg.get('speaker', '?')}] {seg.get('text', '')}")

    except requests.HTTPError as exc:
        sys.exit(f"[ERREUR API] {exc.response.status_code} - {exc.response.text}")
    except Exception as exc:
        sys.exit(f"[ERREUR] {exc}")


if __name__ == "__main__":
    main()