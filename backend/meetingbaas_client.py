"""
meetingbaas_client.py
----------------------
Client HTTP pour l'API Meeting BaaS v2 : création, suivi et suppression de bots.
Ne contient aucune logique de parsing de transcript ni d'enregistrement en base
(voir transcript.py et save_meeting.py).
"""

import time

import requests
API_BASE_URL = "https://api.meetingbaas.com/v2"
POLL_INTERVAL_SECONDS = 15
POLL_TIMEOUT_SECONDS = 60 * 60
EXTRA_WAIT_AFTER_END_SECONDS = 5 * 60

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

    while time.time() - start < POLL_TIMEOUT_SECONDS:
        status = get_bot_status(api_key, bot_id)
        state = status.get("status", "unknown")
        has_video = bool(status.get("video"))
        print(f"[STATUS] {state}" + (" (vidéo disponible)" if has_video else ""))

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
