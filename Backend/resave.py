import argparse
import sys

from config import get_meeting_baas_api_key
from meetingbaas_client import get_bot_status, DEFAULT_BOT_NAME
from save_meeting import save_meeting


def main():
    parser = argparse.ArgumentParser(description="Réenregistre en base une réunion déjà traitée par Meeting BaaS.")
    parser.add_argument("bot_id")
    parser.add_argument("--bot-name", default=DEFAULT_BOT_NAME)
    args = parser.parse_args()

    try:
        api_key = get_meeting_baas_api_key()
    except EnvironmentError as exc:
        sys.exit(f"[ERREUR] {exc}")

    result = get_bot_status(api_key, args.bot_id)
    saved = save_meeting(result, bot_name=args.bot_name)
    print(f"[OK] Recap enregistré en base (id={saved['id']}, créé le {saved['created_at']}).")


if __name__ == "__main__":
    main()
