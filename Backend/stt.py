from pathlib import Path
import os
import subprocess
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

def convert_to_wav(input_path):
    wav_path = input_path.with_suffix(".wav")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-ar", "16000",
            "-ac", "1",
            str(wav_path),
        ],
        check=True,
        capture_output=True,
    )
    return wav_path

def callapi(file_path):
    wav_path = convert_to_wav(file_path)
    try:
        with open(wav_path, "rb") as f:
            translation = client.audio.transcriptions.create(
                file=(wav_path.name, f.read()),
                model="whisper-large-v3",
                prompt="Specify context or spelling",
                response_format="json",
                temperature=0.0
            )
    finally:
        wav_path.unlink(missing_ok=True)

    print(translation.text)
    return translation.text