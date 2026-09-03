import json
import os
import wave
from pathlib import Path

import webrtcvad
from together import Together

_BASE_DIR = Path(__file__).resolve().parent.parent
_VAD_FRAME_DURATION_MS = 30
_VAD_AGGRESSIVENESS = 3
_MIN_SPEECH_RATIO = 0.10

with open(_BASE_DIR / "moderator_context.txt", "r") as moderator_context_file:
    moderator_context = moderator_context_file.read()

client = Together()


class NoSpeechDetectedError(Exception):
    pass


def has_speech(wav_path: Path) -> bool:
    vad = webrtcvad.Vad(_VAD_AGGRESSIVENESS)
    with wave.open(str(wav_path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        pcm_data = wav_file.readframes(wav_file.getnframes())

    frame_bytes = int(sample_rate * _VAD_FRAME_DURATION_MS / 1000) * 2
    total_frames = 0
    speech_frames = 0
    for start in range(0, len(pcm_data) - frame_bytes + 1, frame_bytes):
        frame = pcm_data[start : start + frame_bytes]
        total_frames += 1
        if vad.is_speech(frame, sample_rate):
            speech_frames += 1

    if total_frames == 0:
        return False
    return (speech_frames / total_frames) >= _MIN_SPEECH_RATIO


def verify_report(transcript: str, report: dict) -> dict:
    payload = json.dumps({"transcript": transcript, "report": report}, ensure_ascii=False)

    verification = client.chat.completions.create(
        model=os.environ["CLASSIFIER_MODEL"],
        messages=[
            {"role": "system", "content": moderator_context},
            {"role": "user", "content": payload},
        ],
        temperature=0,
        max_tokens=4096,
        stream=True,
        response_format={"type": "json_object"},
        reasoning={"enabled": False},
    )

    full_content = ""
    for chunk in verification:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            full_content += delta.content

    return json.loads(full_content)
