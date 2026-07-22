"""
transcript.py
-------------
Téléchargement et parsing du transcript diarisé renvoyé par Meeting BaaS.

La réponse d'un bot terminé contient des URLs S3 présignées ("transcription",
"raw_transcription", "diarization") plutôt que du contenu direct. Ce module
télécharge ces fichiers et les transforme en une liste de segments
{speaker, start, end, text} exploitable par le reste de l'application.
"""

import json
from pathlib import Path

import requests
DOWNLOADABLE_URL_FIELDS = ("transcription", "raw_transcription", "diarization")
DEBUG_DUMP_DIR = Path(__file__).resolve().parent / "debug_dumps"

UNRESOLVED_SPEAKER_LABELS = (None, "", "unknown", "inconnu")


def _download_url_field(payload: dict, key: str) -> None:
    """Télécharge le champ `key` s'il contient une URL, et sauvegarde le brut sur disque
    (dans DEBUG_DUMP_DIR) pour permettre l'inspection manuelle du format réel."""
    url = payload.get(key)
    if not isinstance(url, str) or not url.startswith("http"):
        return

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"[WARN] Téléchargement de '{key}' impossible : {e}")
        return

    DEBUG_DUMP_DIR.mkdir(exist_ok=True)
    dump_path = DEBUG_DUMP_DIR / f"{key}.raw.txt"
    dump_path.write_bytes(r.content)
    print(f"[DEBUG] '{key}' téléchargé ({len(r.content)} octets) -> {dump_path}")

    try:
        payload[key] = r.json()
        return
    except ValueError:
        pass

    # Cas JSONL (diarization.jsonl) : un objet JSON par ligne.
    lines = [line for line in r.text.splitlines() if line.strip()]
    try:
        payload[key] = [json.loads(line) for line in lines]
    except ValueError as e:
        print(f"[WARN] '{key}' n'est ni du JSON ni du JSONL valide : {e}")
        payload[key] = r.text


def load_transcription_if_needed(payload: dict) -> dict:
    """Télécharge transcription, raw_transcription et diarization (URLs S3 présignées)
    et remplace chaque champ par son contenu parsé (dict/list) au lieu de l'URL brute.
    Idempotent : un champ déjà téléchargé (donc plus une URL) est ignoré."""
    for key in DOWNLOADABLE_URL_FIELDS:
        _download_url_field(payload, key)
    return payload


def _words_to_text(words) -> str:
    """Joint une liste de mots {word|text, start, end} en une phrase."""
    if not isinstance(words, list):
        return ""
    parts = []
    for w in words:
        if isinstance(w, dict):
            parts.append(w.get("word") or w.get("text") or "")
        else:
            parts.append(str(w))
    return " ".join(p for p in parts if p)


def _normalize_segments(raw) -> list:
    """Convertit le contenu de output_transcription.json en segments {speaker, start, end, text}.

    Format réel observé : {"bot_id", "provider", "result": {"utterances": [
        {"text", "start", "end", "speaker", "words": [{"word", "start", "end"}, ...]}
    ]}}. `speaker` vaut parfois "Unknown" (chevauchement de parole non résolu par Gladia).
    """
    if raw is None:
        return []

    if isinstance(raw, dict):
        raw = raw.get("result", raw)
        raw = raw.get("utterances") or raw.get("segments") or raw.get("transcript") or []

    if not isinstance(raw, list):
        return []

    segments = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        speaker = item.get("speaker") or item.get("speaker_name")
        if isinstance(speaker, int):
            speaker = f"Speaker {speaker}"
        if not isinstance(speaker, str) or speaker.strip().lower() in UNRESOLVED_SPEAKER_LABELS:
            speaker = None  # sera résolu via diarization.jsonl si possible, sinon "Inconnu"

        text = item.get("text") or ""
        start = item.get("start")
        end = item.get("end")

        if not text or start is None or end is None:
            words = item.get("words")
            if isinstance(words, list) and words:
                if not text:
                    text = _words_to_text(words)
                first_word = words[0] if isinstance(words[0], dict) else {}
                last_word = words[-1] if isinstance(words[-1], dict) else {}
                start = start if start is not None else first_word.get("start")
                end = end if end is not None else last_word.get("end")

        if not text:
            continue

        segments.append({"speaker": speaker, "start": start, "end": end, "text": text})

    return segments


def _diarization_frames(raw) -> list:
    """Convertit diarization.jsonl (liste de {speaker, start_time, end_time}) en tuples
    (start, end, speaker), utilisés pour résoudre les speakers non identifiés."""
    if not isinstance(raw, list):
        return []
    frames = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        speaker = item.get("speaker")
        start = item.get("start_time", item.get("start"))
        end = item.get("end_time", item.get("end"))
        if not speaker or start is None or end is None:
            continue
        try:
            frames.append((float(start), float(end), speaker))
        except (TypeError, ValueError):
            continue
    return frames


def _best_speaker_for_range(start, end, frames: list) -> str | None:
    """Retourne le speaker dont les frames de diarization recouvrent le plus [start, end]."""
    if start is None or end is None or not frames:
        return None
    start, end = float(start), float(end)
    overlap_by_speaker = {}
    for f_start, f_end, speaker in frames:
        overlap = min(end, f_end) - max(start, f_start)
        if overlap > 0:
            overlap_by_speaker[speaker] = overlap_by_speaker.get(speaker, 0) + overlap
    if not overlap_by_speaker:
        return None
    return max(overlap_by_speaker, key=overlap_by_speaker.get)


def resolve_unknown_speakers(segments: list, diarization_raw) -> list:
    """Comble les segments sans speaker identifié en s'appuyant sur diarization.jsonl
    (recouvrement temporel), puis retombe sur 'Inconnu' si toujours non résolu."""
    frames = _diarization_frames(diarization_raw)
    for seg in segments:
        if seg["speaker"] is None and frames:
            seg["speaker"] = _best_speaker_for_range(seg["start"], seg["end"], frames)
        if not seg["speaker"]:
            seg["speaker"] = "Inconnu"
    return segments


def extract_diarized_transcript(payload: dict) -> list:
    """Point d'entrée principal : extrait les segments diarisés depuis une réponse bot
    dont `transcription`/`diarization` ont déjà été téléchargés (load_transcription_if_needed)."""
    segments = _normalize_segments(payload.get("transcription"))
    if not segments:
        return []
    return resolve_unknown_speakers(segments, payload.get("diarization"))


def group_by_speaker(segments: list) -> dict:
    grouped = {}
    for seg in segments:
        speaker = seg["speaker"]
        grouped.setdefault(speaker, []).append(seg["text"])
    return {speaker: " ".join(t for t in texts if t) for speaker, texts in grouped.items()}


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
    if human_names:
        return ", ".join(human_names)
    return fallback_name


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
