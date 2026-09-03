import requests

UNRESOLVED_SPEAKER_LABELS = ("", "unknown", "inconnu")


def load_transcription_if_needed(payload: dict) -> dict:
    """Télécharge le champ `transcription` s'il s'agit encore d'une URL S3 présignée
    et le remplace par son contenu JSON parsé. Idempotent."""
    url = payload.get("transcription")
    if isinstance(url, str) and url.startswith("http"):
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        payload["transcription"] = response.json()
    return payload


def extract_diarized_transcript(payload: dict) -> list:
    """Extrait les segments diarisés depuis une réponse bot dont `transcription` a déjà
    été téléchargée (load_transcription_if_needed)."""
    raw = payload.get("transcription")
    if not isinstance(raw, dict):
        return []

    utterances = raw.get("result", {}).get("utterances", [])
    segments = []
    for item in utterances:
        speaker = item.get("speaker") or ""
        if str(speaker).strip().lower() in UNRESOLVED_SPEAKER_LABELS:
            speaker = "Inconnu"

        segments.append(
            {
                "speaker": speaker,
                "start": item.get("start"),
                "end": item.get("end"),
                "text": item.get("text", ""),
            }
        )

    return segments


def build_transcript_text(segments: list) -> str:
    """Texte brut 'speaker: texte' à partir des segments diarisés."""
    return "\n".join(f"{segment['speaker']}: {segment['text']}" for segment in segments)


def build_speakers_list(segments: list) -> list:
    """Liste des intervenants au format attendu par la base, à partir de la diarisation."""
    names = sorted({segment["speaker"] for segment in segments})
    return [{"id": index, "names": name, "user_id": None} for index, name in enumerate(names)]


def build_speakers_from_participants(participants: list) -> list:
    """Liste des speakers à partir des infos participants MeetingBaaS (secours quand
    aucun segment diarisé n'est disponible)."""
    speakers = []
    for index, participant in enumerate(participants):
        name = participant.get("name") or participant.get("display_name") or "Inconnu"
        speakers.append({"id": index, "names": name, "user_id": None})
    return speakers


def build_meeting_name(participants: list, bot_name: str, fallback_name: str) -> str:
    """Nom du recap à partir des participants humains (hors bot)."""
    human_names = [
        participant.get("name") or participant.get("display_name") or "Inconnu"
        for participant in participants
        if (participant.get("name") or participant.get("display_name")) != bot_name
    ]
    return ", ".join(human_names) if human_names else fallback_name
