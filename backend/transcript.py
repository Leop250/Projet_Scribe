"""
transcript.py
-------------
Téléchargement et parsing du transcript diarisé renvoyé par Meeting BaaS.

La réponse d'un bot terminé contient une URL S3 présignée dans le champ
"transcription" plutôt que le contenu direct. Ce module télécharge ce
fichier et le transforme en une liste de segments {speaker, start, end,
text} exploitable par le reste de l'application.

Format réel observé : {"bot_id", "provider", "result": {"utterances": [
    {"text", "start", "end", "speaker"}, ...
]}}. `speaker` vaut parfois "Unknown" quand Gladia n'a pas su l'identifier.
"""

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
    """Point d'entrée principal : extrait les segments diarisés depuis une réponse bot
    dont `transcription` a déjà été téléchargée (load_transcription_if_needed)."""
    raw = payload.get("transcription")
    if not isinstance(raw, dict):
        return []

    utterances = raw.get("result", {}).get("utterances", [])
    segments = []
    for item in utterances:
        speaker = item.get("speaker") or ""
        if str(speaker).strip().lower() in UNRESOLVED_SPEAKER_LABELS:
            speaker = "Inconnu"

        segments.append({
            "speaker": speaker,
            "start": item.get("start"),
            "end": item.get("end"),
            "text": item.get("text", ""),
        })

    return segments


def group_by_speaker(segments: list) -> dict:
    grouped = {}
    for seg in segments:
        grouped.setdefault(seg["speaker"], []).append(seg["text"])
    return {speaker: " ".join(texts) for speaker, texts in grouped.items()}


def build_transcript_text(segments: list) -> str:
    """Construit un texte brut 'speaker: texte' à partir des segments diarisés."""
    return "\n".join(f"{seg['speaker']}: {seg['text']}" for seg in segments)


def build_speakers_list(segments: list) -> list:
    """Construit la liste des intervenants au format attendu par la base, à partir de la diarisation."""
    names = sorted({seg["speaker"] for seg in segments})
    return [{"id": i, "names": name, "user_id": None} for i, name in enumerate(names)]


def build_speakers_from_participants(participants: list) -> list:
    """Construit la liste des speakers à partir des vraies infos participants Meeting BaaS
    (utilisé en secours quand aucun segment diarisé n'est disponible)."""
    speakers = []
    for i, p in enumerate(participants):
        name = p.get("name") or p.get("display_name") or "Inconnu"
        speakers.append({"id": i, "names": name, "user_id": None})
    return speakers


def build_meeting_name(participants: list, bot_name: str, fallback_name: str) -> str:
    """Construit le nom du recap à partir des participants humains (hors bot)."""
    human_names = [
        p.get("name") or p.get("display_name") or "Inconnu"
        for p in participants
        if (p.get("name") or p.get("display_name")) != bot_name
    ]
    return ", ".join(human_names) if human_names else fallback_name


def print_diarized_transcript(segments: list) -> None:
    if not segments:
        print("Aucun transcript diarisé trouvé dans la réponse.")
        return

    print(f"\nTranscript ({len(segments)} segment(s)) :")
    for seg in segments:
        ts = f"[{seg['start']}s - {seg['end']}s]" if seg["start"] is not None else ""
        print(f"{ts} {seg['speaker']} : {seg['text']}")

    print("\nPar intervenant :")
    for speaker, text in group_by_speaker(segments).items():
        print(f"- {speaker} : {text}")
