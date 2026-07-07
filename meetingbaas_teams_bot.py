#!/usr/bin/env python3
"""
meetingbaas_teams_bot.py
-------------------------
Envoie un bot Meeting BaaS (API v2) dans une réunion Microsoft Teams
pour l'enregistrer, puis récupère le résultat.

Compatible avec le tier gratuit / trial de Meeting BaaS v2 :
- Pas de "speaking bot" (fonctionnalité payante / plus lourde),
  uniquement enregistrement (couvert par le free trial).
- La transcription est désactivée par défaut : en v2, la transcription
  fonctionne en mode "Bring Your Own Key" (il faut fournir sa propre clé
  Gladia). Utilise --transcribe + --gladia-key si tu as une clé Gladia
  gratuite (https://app.gladia.io) et veux activer la transcription.
- Un seul appel API pour créer le bot, puis polling léger (pas de
  serveur webhook à héberger) pour rester simple à tester.

Prérequis :
    pip install requests python-dotenv --break-system-packages

Utilisation :
    1. Crée un fichier .env à côté du script contenant :
         MEETING_BAAS_API_KEY=votre-cle-api-v2
    2. Ajoute .env à ton .gitignore pour ne jamais le committer.
    3. Lance (enregistrement seul, sans transcription) :
         python3 meetingbaas_teams_bot.py "https://teams.live.com/meet/..."
       Ou avec transcription (nécessite une clé Gladia) :
         python3 meetingbaas_teams_bot.py "https://teams.live.com/meet/..." \
             --transcribe --gladia-key "votre-cle-gladia"

Récupère ta clé API v2 gratuite sur https://dashboard.meetingbaas.com
"""

import sys
import time
import argparse
import requests

from config import get_meeting_baas_api_key, get_gladia_api_key

API_BASE_URL = "https://api.meetingbaas.com/v2"
POLL_INTERVAL_SECONDS = 15   # espace les appels pour rester dans les limites du plan gratuit
POLL_TIMEOUT_SECONDS = 60 * 60  # abandonne le polling après 1h max


def create_bot(api_key: str, meeting_url: str, bot_name: str) -> str:
    """Envoie un bot dans la réunion via l'API v2. Retourne le bot_id.

    Note : la transcription intégrée de Meeting BaaS (BYOK) n'est pas
    disponible sur le plan gratuit (erreur FST_ERR_BYOK_TRANSCRIPTION_NOT_ENABLED_ON_PLAN).
    On enregistre donc seulement la réunion ici ; la transcription est
    faite séparément via l'API Gladia (voir transcribe_with_gladia).
    """
    url = f"{API_BASE_URL}/bots"
    headers = {
        "Content-Type": "application/json",
        "x-meeting-baas-api-key": api_key,
    }
    payload = {
        "meeting_url": meeting_url,
        "bot_name": bot_name,
        "recording_mode": "speaker_view",
        "automatic_leave": {"waiting_room_timeout": 600},
        "transcription_enabled": False,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    bot_data = data.get("data", data)
    bot_id = bot_data.get("bot_id") or bot_data.get("id")
    if not bot_id:
        raise RuntimeError(f"Réponse inattendue de l'API : {data}")

    print(f"[OK] Bot créé avec succès. bot_id = {bot_id}")
    return bot_id


GLADIA_API_BASE = "https://api.gladia.io/v2"


def transcribe_with_gladia(gladia_key: str, audio_url: str) -> str:
    """Envoie l'URL audio directement à Gladia (indépendamment de Meeting BaaS)
    et attend le texte de la transcription complète."""
    headers = {"Content-Type": "application/json", "x-gladia-key": gladia_key}

    print("[INFO] Envoi de l'audio à Gladia pour transcription...")
    response = requests.post(
        f"{GLADIA_API_BASE}/transcription",
        headers=headers,
        json={"audio_url": audio_url, "diarization": True},
        timeout=30,
    )
    response.raise_for_status()
    job = response.json()
    job_id = job["id"]

    start = time.time()
    while time.time() - start < 20 * 60:  # jusqu'à 20 min pour une réunion longue
        poll = requests.get(
            f"{GLADIA_API_BASE}/transcription/{job_id}", headers=headers, timeout=30
        )
        poll.raise_for_status()
        result = poll.json()
        state = result.get("status")
        print(f"[GLADIA] {state}")

        if state == "done":
            return result["result"]["transcription"]["full_transcript"]
        if state == "error":
            raise RuntimeError(f"Transcription Gladia échouée : {result}")

        time.sleep(10)

    raise TimeoutError("Transcription Gladia trop longue, abandon.")


def get_bot_status(api_key: str, bot_id: str) -> dict:
    """Récupère l'état actuel du bot (statut, enregistrement, transcript)."""
    url = f"{API_BASE_URL}/bots/{bot_id}"
    headers = {"x-meeting-baas-api-key": api_key}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("data", data)


def remove_bot(api_key: str, bot_id: str) -> None:
    """Force le bot à quitter la réunion (utile si le script est interrompu)."""
    url = f"{API_BASE_URL}/bots/{bot_id}"
    headers = {"x-meeting-baas-api-key": api_key}
    try:
        requests.delete(url, headers=headers, timeout=30)
        print(f"[INFO] Bot {bot_id} retiré de la réunion.")
    except requests.RequestException as exc:
        print(f"[WARN] Impossible de retirer le bot proprement : {exc}")


def wait_for_completion(api_key: str, bot_id: str) -> dict:
    """Poll périodiquement jusqu'à ce que l'enregistrement soit réellement prêt.

    Important : le statut peut passer à 'call_ended' avant que le lien
    d'enregistrement (upload + traitement côté serveur) soit disponible.
    On continue donc de poller un peu après call_ended, jusqu'à ce que
    le champ 'recording' soit effectivement rempli.
    """
    start = time.time()
    print("[INFO] En attente de la fin de la réunion...")

    ended_since = None
    EXTRA_WAIT_AFTER_END_SECONDS = 5 * 60  # jusqu'à 5 min après la fin pour l'upload

    while time.time() - start < POLL_TIMEOUT_SECONDS:
        status = get_bot_status(api_key, bot_id)
        state = status.get("status", "unknown")
        has_video = bool(status.get("video"))
        print(f"[STATUS] {state}" + (" (vidéo disponible)" if has_video else ""))

        if state in ("failed", "error", "bot.failed"):
            raise RuntimeError(f"Le bot a échoué : {status}")

        if state in ("call_ended", "complete", "completed", "bot.completed"):
            if has_video:
                return status
            if ended_since is None:
                ended_since = time.time()
                print("[INFO] Réunion terminée, en attente de la finalisation de l'enregistrement...")
            elif time.time() - ended_since > EXTRA_WAIT_AFTER_END_SECONDS:
                print("[WARN] Toujours pas de lien après 5 min, retour du dernier statut connu.")
                return status

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError("Délai d'attente dépassé sans obtenir de résultat final.")


def main():
    parser = argparse.ArgumentParser(
        description="Connecte un bot Meeting BaaS (v2) à une réunion Teams pour l'enregistrer."
    )
    parser.add_argument("meeting_url", nargs="?", default=None,
                         help="URL de la réunion (Teams, Google Meet, Zoom)")
    parser.add_argument(
        "--check-bot-id", default=None,
        help="Ne crée pas de nouveau bot : vérifie juste le résultat d'un bot_id existant"
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="Affiche la réponse JSON brute complète (utile pour déboguer les noms de champs)"
    )
    parser.add_argument(
        "--bot-name", default="AI Notetaker", help="Nom affiché du bot dans la réunion"
    )
    parser.add_argument(
        "--transcribe", action="store_true",
        help="Active la transcription (nécessite --gladia-key)"
    )
    parser.add_argument(
        "--gladia-key", default=None,
        help="Clé API Gladia (gratuite sur app.gladia.io) pour la transcription. "
             "Peut aussi être définie via la variable d'environnement GLADIA_API_KEY."
    )
    args = parser.parse_args()

    try:
        api_key = get_meeting_baas_api_key()
    except EnvironmentError as exc:
        sys.exit(f"[ERREUR] {exc}")

    bot_id = None
    try:
        if args.check_bot_id:
            # Mode "juste vérifier" : pas de création de bot, on interroge l'existant
            bot_id = args.check_bot_id
            result = get_bot_status(api_key, bot_id)
            print(f"[STATUS] {result.get('status', 'unknown')}")
        else:
            if not args.meeting_url:
                sys.exit("[ERREUR] Il faut fournir une URL de réunion, ou --check-bot-id.")
            bot_id = create_bot(api_key, args.meeting_url, args.bot_name)
            result = wait_for_completion(api_key, bot_id)

        # Transcription via Gladia (indépendante de Meeting BaaS, contourne
        # la restriction BYOK du plan gratuit)
        if args.transcribe and result.get("audio"):
            try:
                gladia_key = args.gladia_key or get_gladia_api_key()
            except EnvironmentError:
                gladia_key = None
            if not gladia_key:
                print(
                    "[WARN] --transcribe demandé mais aucune clé Gladia trouvée "
                    "(--gladia-key ou GLADIA_API_KEY). Transcription ignorée."
                )
            else:
                try:
                    result["transcription"] = transcribe_with_gladia(
                        gladia_key, result["audio"]
                    )
                except Exception as exc:
                    print(f"[WARN] Échec de la transcription Gladia : {exc}")

        if args.raw:
            import json
            print("\n=== Réponse JSON brute ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))

        print("\n=== Résultat ===")
        print(f"Vidéo          : {result.get('video', 'non disponible')}")
        print(f"Audio          : {result.get('audio', 'non disponible')}")
        print(f"Transcript     : {result.get('transcription') or 'non disponible (transcription désactivée : relance avec --transcribe --gladia-key)'}")
        print(f"Durée (s)      : {result.get('duration_seconds', 'n/a')}")

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