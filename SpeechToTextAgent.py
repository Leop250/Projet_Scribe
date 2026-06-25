from dotenv import load_dotenv
import requests
import os
import time

load_dotenv()


class SpeechToTextAgent:
    BASE = "https://api.meetingbaas.com/v2"

    def __init__(self):
        self.api_key = os.getenv("MEETING_BAAS_API_KEY")
        print(repr(self.api_key))  # verif que la cle est bien chargee
        self.headers = {
            "x-meeting-baas-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    # --- Point d'entree appele par process.py -----------------------------
    def transcribe_meeting(self, meeting_url, poll_interval: int = 30, timeout: int = 7200):
        """Lance le bot, attend la fin de la reunion + le traitement,
        puis renvoie la transcription sous forme de texte."""
        bot_id = self._launch_bot(meeting_url)
        return self._wait_for_transcript(bot_id, poll_interval, timeout)

    # --- 1) Creation du bot ------------------------------------------------
    def _launch_bot(self, meeting_url) -> str:
        payload = {
            "meeting_url": meeting_url,
            "bot_name": "Notetaker",
            "transcription_enabled": True,
            "transcription_config": {"provider": "deepgram"},
            "custom_params": {
                "summarization": True,
                "summarization_config": {"type": "bullet_points"},
            },
        }
        r = requests.post(f"{self.BASE}/bots", json=payload, headers=self.headers)
        print("POST /v2/bots ->", r.status_code)
        r.raise_for_status()
        bot_id = r.json()["data"]["bot_id"]
        print(f"Bot lance, id = {bot_id}")
        return bot_id

    # --- 2) Attente de la transcription (polling) --------------------------
    def _wait_for_transcript(self, bot_id: str, poll_interval: int, timeout: int):
        deadline = time.time() + timeout
        first = True
        while time.time() < deadline:
            bot = self._get_bot(bot_id)

            if first:
                # On affiche la structure reelle une fois, pour pouvoir ajuster
                print("--- reponse brute du bot (pour reference) ---")
                print(bot)
                print("---------------------------------------------")
                first = False

            data = bot.get("data", bot)  # v2 enveloppe dans 'data'
            status = data.get("status")
            print(f"Statut du bot : {status}")

            transcript = self._extract_transcript(data)
            if transcript:
                print("Transcription prete !")
                return transcript

            # Si le bot est parti/termine mais qu'on n'a rien trouve : on s'arrete
            if status in ("error", "failed"):
                raise RuntimeError(f"Le bot a echoue (statut={status}). Reponse : {data}")

            print(f"Pas encore prete, nouvelle verification dans {poll_interval}s...")
            time.sleep(poll_interval)

        raise TimeoutError("Transcription non disponible avant l'expiration du delai.")

    # --- Appel GET pour recuperer l'etat du bot ----------------------------
    def _get_bot(self, bot_id: str) -> dict:
        r = requests.get(f"{self.BASE}/bots/{bot_id}", headers=self.headers)
        r.raise_for_status()
        return r.json()

    # --- Extraction defensive de la transcription --------------------------
    def _extract_transcript(self, data: dict):
        # Cas A : une URL vers un fichier JSON (frequent en v2 : champ 'transcription')
        url = data.get("transcription") or data.get("transcript_url")
        if isinstance(url, str) and url.startswith("http"):
            try:
                content = requests.get(url).json()
                return self._format_segments(content)
            except Exception as e:
                print("Echec du telechargement de la transcription :", e)
                return None

        # Cas B : la transcription est directement dans la reponse (liste de segments)
        segments = (
            data.get("transcripts")
            or data.get("transcript")
            or data.get("bot_data", {}).get("transcripts")
        )
        if segments:
            return self._format_segments(segments)

        return None

    # --- Mise en forme : on transforme les segments en texte simple --------
    def _format_segments(self, content):
        # content peut etre une liste de segments, ou un dict contenant cette liste
        if isinstance(content, dict):
            content = (
                content.get("transcripts")
                or content.get("segments")
                or content.get("transcription")
                or []
            )

        lignes = []
        for seg in content:
            speaker = seg.get("speaker", "?")
            # le texte peut etre direct ('text') ou reconstruit depuis les mots
            texte = seg.get("text")
            if not texte and "words" in seg:
                texte = " ".join(w.get("word", "") for w in seg["words"])
            lignes.append(f"{speaker}: {texte or ''}")
        return "\n".join(lignes)