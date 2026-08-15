import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class SpeechToText:
    def __init__(self, model="whisper-large-v3"):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = model

    def transcribe_audio(self, file_path):
        with open(file_path, "rb") as audio_file:
            transcription_response = self.client.audio.transcriptions.create(
                file=(file_path.name, audio_file.read()),
                model=self.model,
                prompt="Specify context or spelling",
                response_format="json",
                temperature=0.0
            )
        print(transcription_response.text)
        return transcription_response.text


_default_speech_to_text = SpeechToText()


def transcribe_audio(file_path):
    return _default_speech_to_text.transcribe_audio(file_path)
