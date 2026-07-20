#!/usr/bin/env python3
"""
meetingbaas_teams_bot.py
-------------------------
Envoie un bot Meeting BaaS (API v2) dans une réunion Microsoft Teams
pour l'enregistrer, puis récupère le résultat — y compris le transcript
diarisé (qui a dit quoi, avec les timestamps) tel qu'il apparaît dans le
Dashboard Meeting BaaS.

Changement par rapport à la version précédente :
- La transcription est désormais demandée directement à la création du
  bot (transcription_enabled=True), via le moteur intégré de Meeting BaaS.
  On n'appelle donc plus l'API Gladia nous-mêmes : le texte diarisé
  (speaker + texte + timestamps) vient tel quel de Meeting BaaS, comme
  dans le Dashboard.
- Attention : sur le plan gratuit, la transcription "Bring Your Own Key"
  (BYOK) peut être refusée par l'API avec l'erreur
  FST_ERR_BYOK_TRANSCRIPTION_NOT_ENABLED_ON_PLAN si le provider demandé
  nécessite une clé externe. Le script essaie d'abord sans préciser de
  provider (moteur par défaut de Meeting BaaS) ; utilise --provider pour
  forcer un autre moteur si besoin (ex: "gladia", "deepgram", ...), ou
  --no-transcription pour revenir au simple enregistrement.
- Le nom exact du champ retourné pour le transcript ("transcript",
  "transcripts" ou "transcription" selon le point d'accès / la version)
  n'est pas garanti stable dans la doc publique v2 : la fonction
  extract_diarized_transcript() cherche donc parmi plusieurs noms
  possibles. Utilise --raw pour vérifier la structure exacte chez toi et
  ajuster si besoin.

Prérequis :
    pip install requests python-dotenv --break-system-packages

Utilisation :
    1. Crée un fichier .env à côté du script contenant :
         MEETING_BAAS_API_KEY=votre-cle-api-v2
    2. Ajoute .env à ton .gitignore pour ne jamais le committer.
    3. Lance (enregistrement + transcription diarisée, moteur par défaut) :
         python3 meetingbaas_teams_bot.py "https://teams.live.com/meet/..."
       Pour forcer un moteur de transcription précis :
         python3 meetingbaas_teams_bot.py "https://teams.live.com/meet/..." \
             --provider deepgram
       Pour désactiver la transcription (enregistrement seul, comme avant) :
         python3 meetingbaas_teams_bot.py "https://teams.live.com/meet/..." \
             --no-transcription
    4. Pour voir l'historique des réunions/bots déjà lancés :
         python3 meetingbaas_teams_bot.py --history
       (ajoute --raw pour voir le JSON complet renvoyé par l'API)

Récupère ta clé API v2 gratuite sur https://dashboard.meetingbaas.com
"""

import sys
import time
import argparse
import requests

from config import get_meeting_baas_api_key

API_BASE_URL = "https://api.meetingbaas.com/v2"
POLL_INTERVAL_SECONDS = 15   # espace les appels pour rester dans les limites du plan gratuit
POLL_TIMEOUT_SECONDS = 60 * 60  # abandonne le polling après 1h max

# Mots-clés utilisés pour repérer dynamiquement d'éventuels champs liés aux
# participants dans les réponses de l'API, dont le nom exact n'est pas
# garanti/documenté publiquement pour tous les plans.
PARTICIPANT_KEY_HINTS = ("participant", "attendee", "speaker")

# Noms de champs possibles pour le transcript diarisé selon l'endpoint /
# la version de l'API (webhook vs GET /bots/{id}).
TRANSCRIPT_KEY_CANDIDATES = ("transcript", "transcripts", "transcription")


DEFAULT_TRANSCRIPTION_PROVIDER = "gladia" # moteur géré nativement par Meeting BaaS


def create_bot(api_key: str, meeting_url: str, bot_name: str,
                transcription_enabled: bool, provider: str | None) -> str:
    """Envoie un bot dans la réunion via l'API v2. Retourne le bot_id.

    Si transcription_enabled=True, demande à Meeting BaaS de transcrire
    et diariser lui-même la réunion (moteur interne, éventuellement
    piloté via `provider`). C'est ce texte-là, diarisé par locuteur, qui
    apparaît dans le Dashboard.

    Important : l'API v2 exige un `transcription_config` (avec un
    provider) dès que transcription_enabled=True, sinon elle renvoie
    FST_ERR_VALIDATION ("transcription_config is required"). On envoie
    donc toujours un provider par défaut (DEFAULT_TRANSCRIPTION_PROVIDER)
    si l'utilisateur n'en précise pas un via --provider. Ce provider est
    appelé par Meeting BaaS en interne (moteur managé, pas d'appel direct
    de notre côté) — c'est ce qui alimente le Dashboard.

    Note : selon le plan, un provider nécessitant ta propre clé (BYOK)
    peut être refusé par l'API (FST_ERR_BYOK_TRANSCRIPTION_NOT_ENABLED_ON_PLAN).
    Si ça arrive, essaie un autre --provider, ou repasse en --no-transcription.
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
        "transcription_enabled": transcription_enabled,
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
    """Récupère l'état actuel du bot (statut, enregistrement, transcript,
    et toute autre métadonnée renvoyée par l'API : participants, durée, etc.)."""
    url = f"{API_BASE_URL}/bots/{bot_id}"
    headers = {"x-meeting-baas-api-key": api_key}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("data", data)


def list_bots_history(api_key: str, limit: int = 20) -> list:
    """Récupère l'historique des bots/réunions déjà lancés via l'API v2."""
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
    """Cherche dans la réponse de l'API toute clé qui ressemble à une
    information de participant (participant_id, attendees, speakers, etc.)."""
    found = {}
    for key, value in payload.items():
        lower_key = key.lower()
        if any(hint in lower_key for hint in PARTICIPANT_KEY_HINTS):
            found[key] = value
    return found


def _normalize_segments(raw) -> list:
    """Ramène différentes formes possibles de transcript à une liste plate
    de segments {speaker, start, end, text}.

    Gère :
      - une liste de segments directement : [{"speaker": ..., "text": ...}, ...]
      - un dict enveloppant : {"segments": [...]} ou {"utterances": [...]}
      - des variantes de noms de clés (start/startTime/start_time, etc.)
    """
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
            # certaines API renvoient une liste de mots plutôt qu'une string
            text = " ".join(
                w.get("text", "") if isinstance(w, dict) else str(w) for w in text
            )
        segments.append({"speaker": speaker, "start": start, "end": end, "text": text})

    return segments


def extract_diarized_transcript(payload: dict) -> list:
    """Cherche parmi les noms de champs candidats et renvoie une liste de
    segments normalisés {speaker, start, end, text}, triés par ordre
    d'apparition (chronologique si les données le sont déjà)."""
    for key in TRANSCRIPT_KEY_CANDIDATES:
        if key in payload and payload[key]:
            segments = _normalize_segments(payload[key])
            if segments:
                return segments
    return []


def group_by_speaker(segments: list) -> dict:
    """Regroupe le texte de chaque locuteur, dans l'ordre chronologique."""
    grouped = {}
    for seg in segments:
        speaker = seg["speaker"]
        grouped.setdefault(speaker, []).append(seg["text"])
    return {speaker: " ".join(t for t in texts if t) for speaker, texts in grouped.items()}


def print_diarized_transcript(segments: list) -> None:
    """Affiche le transcript chronologique horodaté, puis le texte cumulé
    par locuteur."""
    if not segments:
        print(
            "\n[INFO] Aucun transcript diarisé trouvé dans la réponse. "
            "Vérifie que --provider est compatible avec ton plan, ou relance "
            "avec --raw pour inspecter la structure exacte renvoyée par l'API."
        )
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
    """Force le bot à quitter la réunion (utile si le script est interrompu)."""
    url = f"{API_BASE_URL}/bots/{bot_id}"
    headers = {"x-meeting-baas-api-key": api_key}
    try:
        requests.delete(url, headers=headers, timeout=30)
        print(f"[INFO] Bot {bot_id} retiré de la réunion.")
    except requests.RequestException as exc:
        print(f"[WARN] Impossible de retirer le bot proprement : {exc}")


def wait_for_completion(api_key: str, bot_id: str) -> dict:
    """Poll périodiquement jusqu'à ce que l'enregistrement (et le transcript,
    s'il a été demandé) soit réellement prêt.

    Important : le statut peut passer à 'call_ended' avant que le lien
    d'enregistrement ET le transcript (traitement asynchrone côté serveur)
    soient disponibles. On continue donc de poller un peu après call_ended.
    """
    start = time.time()
    print("[INFO] En attente de la fin de la réunion...")

    ended_since = None
    EXTRA_WAIT_AFTER_END_SECONDS = 5 * 60  # jusqu'à 5 min après la fin pour l'upload + la transcription

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
            if has_video:
                return status
            if ended_since is None:
                ended_since = time.time()
                print("[INFO] Réunion terminée, en attente de la finalisation de l'enregistrement/transcript...")
            elif time.time() - ended_since > EXTRA_WAIT_AFTER_END_SECONDS:
                print("[WARN] Toujours pas de lien après 5 min, retour du dernier statut connu.")
                return status

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError("Délai d'attente dépassé sans obtenir de résultat final.")


def print_history(bots: list, raw: bool = False) -> None:
    """Affiche l'historique des bots/réunions de façon lisible."""
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
    parser = argparse.ArgumentParser(
        description="Connecte un bot Meeting BaaS (v2) à une réunion Teams pour l'enregistrer "
                     "et récupérer le transcript diarisé (locuteur + texte)."
    )
    parser.add_argument("meeting_url", nargs="?", default=None,
                         help="URL de la réunion (Teams, Google Meet, Zoom)")
    parser.add_argument(
        "--check-bot-id", default=None,
        help="Ne crée pas de nouveau bot : vérifie juste le résultat d'un bot_id existant"
    )
    parser.add_argument(
        "--history", action="store_true",
        help="Affiche l'historique des bots/réunions déjà lancés"
    )
    parser.add_argument(
        "--history-limit", type=int, default=20,
        help="Nombre maximum de bots à afficher avec --history (défaut : 20)"
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="Affiche la réponse JSON brute complète (utile pour déboguer les noms de champs)"
    )
    parser.add_argument(
        "--bot-name", default="AI Notetaker", help="Nom affiché du bot dans la réunion"
    )
    parser.add_argument(
        "--no-transcription", action="store_true",
        help="Désactive la transcription (enregistrement seul, comme avant)"
    )
    parser.add_argument(
        "--provider", default=None,
        help="Force un moteur de transcription précis côté Meeting BaaS "
             "(ex: 'deepgram', 'gladia', ...). Par défaut, aucun provider n'est "
             "précisé et Meeting BaaS utilise son moteur par défaut."
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
                sys.exit("[ERREUR] Il faut fournir une URL de réunion, --check-bot-id, ou --history.")
            bot_id = create_bot(
                api_key,
                args.meeting_url,
                args.bot_name,
                transcription_enabled=not args.no_transcription,
                provider=args.provider,
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
        print(f"Vidéo          : {result.get('video', 'non disponible')}")
        print(f"Audio          : {result.get('audio', 'non disponible')}")
        print(f"Durée (s)      : {result.get('duration_seconds', 'n/a')}")

        # Transcript diarisé (locuteur + texte), directement depuis Meeting BaaS
        segments = extract_diarized_transcript(result)
        print_diarized_transcript(segments)

        # Autres métadonnées liées aux participants, si disponibles
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