import json
import sys
import argparse

import requests

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
from transcript import load_transcription_if_needed, extract_diarized_transcript, print_diarized_transcript
from save_meeting import save_meeting


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

        participants = bot.get("participants")
        if participants:
            print(f"   Participants   : {participants}")

        if raw:
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

        participants = result.get("participants") or []
        if participants:
            print("\n=== Participants ===")
            print(participants)

        saved = save_meeting(result, bot_name=args.bot_name)
        print(f"\n[OK] Recap enregistré en base (id={saved['id']}, créé le {saved['created_at']}).")

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
