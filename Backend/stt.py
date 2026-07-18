from pathlib import Path
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

def callapi(file_path):
    with open(file_path, "rb") as f:
        translation = client.audio.transcriptions.create(
            file=(file_path.name, f.read()),
            model="whisper-large-v3",
            prompt="Specify context or spelling",
            response_format="json",
            temperature=0.0
        )
    print(translation.text)
    return translation.text