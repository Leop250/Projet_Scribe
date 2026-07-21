import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
print("GROQ_API_KEY vue par le serveur :", repr(os.environ.get("GROQ_API_KEY")))
client = Groq(api_key=os.environ["GROQ_API_KEY"])

with open("agent_context.txt", "r") as f:
    context = f.read()

def generate_report(transcript):
    analyze = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": context
            },
            {
                "role": "user",
                "content": transcript
            }
        ],
        temperature=0,
        max_completion_tokens=4096,
        top_p=0.95,
        stream=False,
        response_format={"type": "json_object"},
        reasoning_format="hidden",
        reasoning_effort="medium"
    )

    return json.loads(analyze.choices[0].message.content)