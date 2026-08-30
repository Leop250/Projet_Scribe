import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from mistralai.client import Mistral

from ai.moderation import NoSpeechDetectedError, has_speech

_BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(_BASE_DIR / ".env")

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])


def convert_to_wav(input_path: Path) -> Path:
    wav_path = input_path.with_suffix(".wav")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_path), "-ar", "16000", "-ac", "1", str(wav_path)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        wav_path.unlink(missing_ok=True)
        raise NoSpeechDetectedError("Fichier audio illisible ou format non supporté.") from error
    return wav_path


def build_diarized_transcript(segments) -> str:
    speaker_labels = {}
    lines = []
    for segment in segments:
        speaker_key = segment.speaker_id or "0"
        if speaker_key not in speaker_labels:
            speaker_labels[speaker_key] = f"Interlocuteur {len(speaker_labels) + 1}"
        text = segment.text.strip()
        if text:
            lines.append(f"{speaker_labels[speaker_key]}: {text}")
    return "\n".join(lines)


def call_speech_to_text_agent(file_path: Path) -> str:
    wav_path = convert_to_wav(file_path)
    try:
        if not has_speech(wav_path):
            raise NoSpeechDetectedError("Aucune parole détectée dans l'enregistrement.")

        with open(wav_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.complete(
                model=os.environ["SPEECH_TO_TEXT_MODEL"],
                file={"file_name": wav_path.name, "content": audio_file},
                diarize=True,
                timestamp_granularities=["segment"],
            )

        result = (
            build_diarized_transcript(transcription.segments)
            if transcription.segments
            else transcription.text.strip()
        )

        if not result:
            raise NoSpeechDetectedError("Aucune parole détectée dans l'enregistrement.")

        return result
    finally:
        wav_path.unlink()
