#!/usr/bin/env python3
"""
vexa_bot.py
-----------
Envoie un bot Vexa AI dans une réunion Google Meet ou Microsoft Teams,
puis récupère le transcript. Suit exactement la doc officielle Vexa :
https://docs.vexa.ai/quickstart

Base URL confirmée dans le Quickstart officiel : https://api.cloud.vexa.ai
(attention : api.vexa.ai, mentionné sur la landing page, ne résout pas)

Endpoints utilisés (doc officielle) :
    POST /bots
        Headers: X-API-Key: <API_KEY>
        Body (Google Meet):
            { "platform": "google_meet", "native_meeting_id": "<abc-defg-hij>" }
        Body (Microsoft Teams, nécessite un passcode) :
            { "platform": "teams", "native_meeting_id": "<NUMERIC_ID>", "passcode": "<PASSCODE>" }

    GET /transcripts/{platform}/{native_meeting_id}
        Headers: X-API-Key: <API_KEY>
        Renvoie les segments transcrits (speaker, texte, horodatage).

Chaque nouveau compte Vexa reçoit 5$ de crédit gratuit (~16h de bot),
sans carte bancaire (https://vexa.ai/get-started).

Prérequis :
    pip install requests python-dotenv --break-system-packages

Utilisation :
    1. Crée un compte sur https://vexa.ai et récupère ta clé API (vx_sk_...)
    2. Ajoute dans ton .env :
         VEXA_API_KEY=vx_sk_...
    3. Google Meet :
         python3 vexa_bot.py google_meet "abc-defg-hij"
    4. Microsoft Teams (nécessite l'ID numérique ET le passcode de la réunion) :
         python3 vexa_bot.py teams "9387167464734" --passcode "qxJanYOcdjN4d6UlGa"
"""

import sys
import time
import argparse
import requests

from config import get_vexa_api_key

API_BASE = "https://api.cloud.vexa.ai"
POLL_INTERVAL_SECONDS = 15
POLL_TIMEOUT_SECONDS = 60 * 60


def create_bot(api_key: str, platform: str, native_meeting_id: str, passcode: str | None) -> dict:
    """POST /bots — suit exactement le format de la doc officielle Vexa."""
    url = f"{API_BASE}/bots"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    payload = {
        "platform": platform,
        "native_meeting_id": native_meeting_id,
        "recording_enabled": True,
        "transcribe_enabled": True,
        "transcription_tier": "realtime",
    }
    if platform == "teams":
        if not passcode:
            raise ValueError("Une réunion Teams nécessite --passcode (voir doc Vexa).")
        payload["passcode"] = passcode

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    print(f"[OK] Bot envoyé dans la réunion {platform}/{native_meeting_id}.")
    return data


def get_transcript(api_key: str, platform: str, native_meeting_id: str) -> dict:
    """GET /transcripts/{platform}/{native_meeting_id} — doc officielle Vexa."""
    url = f"{API_BASE}/transcripts/{platform}/{native_meeting_id}"
    headers = {"X-API-Key": api_key}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def poll_transcript(api_key: str, platform: str, native_meeting_id: str) -> dict:
    """Poll le transcript jusqu'à obtenir des segments, ou jusqu'au timeout."""
    start = time.time()
    print("[INFO] En attente des premiers segments de transcript...")

    while time.time() - start < POLL_TIMEOUT_SECONDS:
        data = get_transcript(api_key, platform, native_meeting_id)
        segments = data.get("data", data).get("transcripts") or data.get("segments") or []
        print(f"[STATUS] {len(segments)} segment(s) reçu(s) pour l'instant.")

        if segments:
            return data

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError("Aucun segment de transcript reçu avant le délai imparti.")


def main():
    parser = argparse.ArgumentParser(
        description="Envoie un bot Vexa AI dans une réunion et récupère le transcript."
    )
    parser.add_argument("platform", choices=["google_meet", "teams"],
                         help="Plateforme de la réunion")
    parser.add_argument("native_meeting_id",
                         help="Code Google Meet (ex: abc-defg-hij) ou ID numérique Teams")
    parser.add_argument("--passcode", default=None,
                         help="Passcode de la réunion Teams (requis pour teams)")
    args = parser.parse_args()

    try:
        api_key = get_vexa_api_key()
    except EnvironmentError as exc:
        sys.exit(f"[ERREUR] {exc}")

    try:
        create_bot(api_key, args.platform, args.native_meeting_id, args.passcode)
        result = poll_transcript(api_key, args.platform, args.native_meeting_id)

        print("\n=== Transcript ===")
        segments = result.get("data", result).get("transcripts") or result.get("segments") or []
        for seg in segments:
            speaker = seg.get("speaker", "?")
            text = seg.get("text", "")
            print(f"[{speaker}] {text}")

    except requests.HTTPError as exc:
        sys.exit(f"[ERREUR API] {exc.response.status_code} - {exc.response.text}")
    except Exception as exc:
        sys.exit(f"[ERREUR] {exc}")


if __name__ == "__main__":
    main()