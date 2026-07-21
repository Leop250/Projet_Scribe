
import sys
import time
import argparse
import requests

from config import get_meeting_baas_api_key

API_BASE_URL = "https://api.meetingbaas.com/v2"
POLL_INTERVAL_SECONDS = 15
POLL_TIMEOUT_SECONDS = 60 * 60

PARTICIPANT_KEY_HINTS = ("participant", "attendee", "speaker")
TRANSCRIPT_KEY_CANDIDATES = ("transcript", "transcripts", "transcription")

DEFAULT_TRANSCRIPTION_PROVIDER = "gladia"
DEFAULT_RECORDING_MODE = "audio_only"
DEFAULT_BOT_NAME = "Scribe"


def create_bot(api_key: str, meeting_url: str, bot_name: str,
                transcription_enabled: bool, provider: str | None,
                recording_mode: str = DEFAULT_RECORDING_MODE) -> str:
    url = f"{API_BASE_URL}/bots"
    headers = {
        "Content-Type": "application/json",
        "x-meeting-baas-api-key": api_key,
    }
    payload = {
        "meeting_url": meeting_url,
        "bot_name": bot_name,
        "recording_mode": recording_mode,
        "automatic_leave": {"waiting_room_timeout": 600},
        "transcription_enabled": transcription_enabled,
        "take_screenshots": False, 
    }
    if transcription_enabled:
        payload["transcription_config"] = {"provider": provider or DEFAULT_TRANSCRIPTION_PROVIDER}

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    bot_data = data.get("data", data)
    bot_id = bot_data.get("bot_id") or bot_data.get("id")
    if not bot_id:
        raise RuntimeError(f"Réponse inattendue de l'API : {data}")

    print(f"[OK] Bot créé avec succès. bot_id = {bot_id}")
    return bot_id


def get_bot_status(api_key: str, bot_id: str) -> dict:
    url = f"{API_BASE_URL}/bots/{bot_id}"
    headers = {"x-meeting-baas-api-key": api_key}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("data", data)


def list_bots_history(api_key: str, limit: int = 20) -> list:
    url = f"{API_BASE_URL}/bots"
    headers = {"x-meeting-baas-api-key": api_key}
    params = {"limit": limit}

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    bots = data.get("data", data)
    if isinstance(bots, dict):
        bots = bots.get("bots") or bots.get("items") or []
    if not isinstance(bots, list):
        bots = []

    return bots


def extract_participant_info(payload: dict) -> dict:
    found = {}
    for key, value in payload.items():
        lower_key = key.lower()
        if any(hint in lower_key for hint in PARTICIPANT_KEY_HINTS):
            found[key] = value
    return found


def _normalize_segments(raw) -> list:
    if raw is None:
        return []

    if isinstance(raw, dict):
        raw = raw.get("segments") or raw.get("utterances") or raw.get("items") or []

    if not isinstance(raw, list):
        return []

    segments = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        speaker = (
            item.get("speaker")
            or item.get("speaker_name")
            or item.get("participant")
            or item.get("name")
            or "Inconnu"
        )
        text = item.get("text") or item.get("transcript") or item.get("words") or ""
        start = item.get("start") or item.get("startTime") or item.get("start_time")
        end = item.get("end") or item.get("endTime") or item.get("end_time")
        if isinstance(text, list):
            text = " ".join(
                w.get("text", "") if isinstance(w, dict) else str(w) for w in text
            )
        segments.append({"speaker": speaker, "start": start, "end": end, "text": text})

    return segments


def load_transcription_if_needed(payload: dict) -> dict:
    url = payload.get("transcription")
    if isinstance(url, str) and url.startswith("http"):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            payload["transcription"] = r.json()
        except Exception as e:
            print(f"[WARN] Chargement transcription impossible: {e}")
    return payload


def extract_diarized_transcript(payload: dict) -> list:
    for key in TRANSCRIPT_KEY_CANDIDATES:
        if key in payload and payload[key]:
            segments = _normalize_segments(payload[key])
            if segments:
                return segments
    return []


def group_by_speaker(segments: list) -> dict:
    grouped = {}
    for seg in segments:
        speaker = seg["speaker"]
        grouped.setdefault(speaker, []).append(seg["text"])
    return {speaker: " ".join(t for t in texts if t) for speaker, texts in grouped.items()}


def print_diarized_transcript(segments: list) -> None:
    if not segments:
        print("\n[INFO] Aucun transcript diarisé trouvé dans la réponse.")
        return

    print(f"\n=== Transcript chronologique ({len(segments)} segment(s)) ===")
    for seg in segments:
        ts = ""
        if seg["start"] is not None:
            ts = f"[{seg['start']}s"
            if seg["end"] is not None:
                ts += f" - {seg['end']}s]"
            else:
                ts += "]"
        print(f"{ts} {seg['speaker']} : {seg['text']}")

    print("\n=== Texte cumulé par intervenant ===")
    for speaker, text in group_by_speaker(segments).items():
        print(f"\n--- {speaker} ---")
        print(text)


def remove_bot(api_key: str, bot_id: str) -> None:
    url = f"{API_BASE_URL}/bots/{bot_id}"
    headers = {"x-meeting-baas-api-key": api_key}
    try:
        requests.delete(url, headers=headers, timeout=30)
        print(f"[INFO] Bot {bot_id} retiré de la réunion.")
    except requests.RequestException as exc:
        print(f"[WARN] Impossible de retirer le bot proprement : {exc}")


def wait_for_completion(api_key: str, bot_id: str) -> dict:
    start = time.time()
    print("[INFO] En attente de la fin de la réunion...")

    ended_since = None
    EXTRA_WAIT_AFTER_END_SECONDS = 5 * 60

    while time.time() - start < POLL_TIMEOUT_SECONDS:
        status = get_bot_status(api_key, bot_id)
        state = status.get("status", "unknown")
        has_video = bool(status.get("video"))
        has_transcript = bool(extract_diarized_transcript(status))
        print(
            f"[STATUS] {state}"
            + (" (vidéo disponible)" if has_video else "")
            + (" (transcript disponible)" if has_transcript else "")
        )

        if state in ("failed", "error", "bot.failed"):
            raise RuntimeError(f"Le bot a échoué : {status}")

        if state in ("call_ended", "complete", "completed", "bot.completed"):
            if has_video or status.get("audio"):
                return status
            if ended_since is None:
                ended_since = time.time()
                print("[INFO] Réunion terminée, en attente de la finalisation...")
            elif time.time() - ended_since > EXTRA_WAIT_AFTER_END_SECONDS:
                print("[WARN] Toujours pas de lien après 5 min, retour du dernier statut connu.")
                return status

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError("Délai d'attente dépassé sans obtenir de résultat final.")


def print_history(bots: list, raw: bool = False) -> None:
    if not bots:
        print("[INFO] Aucun bot trouvé dans l'historique.")
        return

    print(f"\n=== Historique des réunions ({len(bots)} bot(s)) ===")
    for i, bot in enumerate(bots, start=1):
        bot_id = bot.get("bot_id") or bot.get("id", "n/a")
        bot_name = bot.get("bot_name", "n/a")
        meeting_url = bot.get("meeting_url", "n/a")
        status = bot.get("status") or bot.get("state", "n/a")
        created_at = bot.get("created_at", "n/a")
        duration = bot.get("duration_seconds", "n/a")

        print(f"\n{i}. bot_id        : {bot_id}")
        print(f"   Nom            : {bot_name}")
        print(f"   URL réunion    : {meeting_url}")
        print(f"   Statut         : {status}")
        print(f"   Créé le        : {created_at}")
        print(f"   Durée (s)      : {duration}")

        participants = extract_participant_info(bot)
        if participants:
            print(f"   Participants   : {participants}")

        segments = extract_diarized_transcript(bot)
        if segments:
            print(f"   Transcript     : {len(segments)} segment(s) diarisé(s) disponible(s)")

        if raw:
            import json
            print(f"   JSON brut      : {json.dumps(bot, ensure_ascii=False)}")


def main():
    parser = argparse.ArgumentParser(description="Envoie Scribe (bot Meeting BaaS) dans une réunion Teams.")
    parser.add_argument("meeting_url", nargs="?", default=None)
    parser.add_argument("--check-bot-id", default=None)
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--history-limit", type=int, default=20)
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--bot-name", default=DEFAULT_BOT_NAME)
    parser.add_argument("--no-transcription", action="store_true")
    parser.add_argument("--provider", default=None)
    parser.add_argument(
        "--recording-mode", default=DEFAULT_RECORDING_MODE,
        choices=["audio_only", "speaker_view", "gallery_view"],
    )
    args = parser.parse_args()

    try:
        api_key = get_meeting_baas_api_key()
    except EnvironmentError as exc:
        sys.exit(f"[ERREUR] {exc}")

    if args.history:
        try:
            bots = list_bots_history(api_key, limit=args.history_limit)
            print_history(bots, raw=args.raw)
        except requests.HTTPError as exc:
            sys.exit(f"[ERREUR API] {exc.response.status_code} - {exc.response.text}")
        except Exception as exc:
            sys.exit(f"[ERREUR] {exc}")
        return

    bot_id = None
    try:
        if args.check_bot_id:
            bot_id = args.check_bot_id
            result = get_bot_status(api_key, bot_id)
            print(f"[STATUS] {result.get('status', 'unknown')}")
        else:
            if not args.meeting_url:
                try:
                    args.meeting_url = input("Colle l'URL de la réunion Teams : ").strip()
                except (EOFError, KeyboardInterrupt):
                    args.meeting_url = ""
                if not args.meeting_url:
                    sys.exit("[ERREUR] Il faut fournir une URL de réunion, --check-bot-id, ou --history.")
            bot_id = create_bot(
                api_key,
                args.meeting_url,
                args.bot_name,
                transcription_enabled=not args.no_transcription,
                provider=args.provider,
                recording_mode=args.recording_mode,
            )
            result = wait_for_completion(api_key, bot_id)

        if args.raw:
            import json
            print("\n=== Réponse JSON brute ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))

        print("\n=== Résultat ===")
        print(f"Bot ID         : {bot_id}")
        print(f"Nom du bot     : {result.get('bot_name', 'n/a')}")
        print(f"URL réunion    : {result.get('meeting_url', 'n/a')}")
        print(f"Créé le        : {result.get('created_at', 'n/a')}")
        print(f"Vidéo          : {result.get('video', 'non disponible (mode audio_only)')}")
        print(f"Audio          : {result.get('audio', 'non disponible')}")
        print(f"Durée (s)      : {result.get('duration_seconds', 'n/a')}")

        result = load_transcription_if_needed(result)
        segments = extract_diarized_transcript(result)
        print_diarized_transcript(segments)

        participants = extract_participant_info(result)
        if participants:
            print("\n=== Autres métadonnées participants ===")
            for key, value in participants.items():
                print(f"{key} : {value}")

    except KeyboardInterrupt:
        print("\n[INFO] Interruption manuelle détectée.")
        if bot_id:
            remove_bot(api_key, bot_id)
        sys.exit(1)
    except requests.HTTPError as exc:
        sys.exit(f"[ERREUR API] {exc.response.status_code} - {exc.response.text}")
    except Exception as exc:
        sys.exit(f"[ERREUR] {exc}")


if __name__ == "__main__":
    main()