import os
import base64
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv("../.env")

api_key = os.environ["MISTRAL_API_KEY"]
model = "voxtral-small-latest"

client = Mistral(api_key=api_key)



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
            content = f.read()
        audio_base64 = base64.b64encode(content).decode("utf-8")

        chat_response = client.chat.complete(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": audio_base64,
                        },
                {
                    "type": "text",
                    "text": "Transcris fidèlement et intégralement ce fichier audio, mot pour mot, dans la langue originale parlée (ne traduis jamais dans une autre langue). Ne résume pas, ne décris pas le contenu. Réponds uniquement avec la transcription brute, dans la langue exacte utilisée par le locuteur."
                }   
                    ]
                }
            ],
        )
        result = chat_response.choices[0].message.content
        print(result)
        return result
    finally:
        os.unlink(wav_path)
