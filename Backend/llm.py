import json
from pathlib import Path
from together import Together

from config import get_together_api_key, get_together_model
client = Together(api_key=get_together_api_key())
TOGETHER_MODEL = get_together_model()
CONTEXT_PATH = Path(__file__).resolve().parent / "agent_context.txt"


with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
    context = f.read()




def generate_report(transcript: str) -> dict:
    analyze = client.chat.completions.create(
        model=TOGETHER_MODEL,
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": transcript},
        ],
        temperature=0,
        max_tokens=4096,
        stream=True,
        response_format={"type": "json_object"},
    )

    full_content = ""
    for chunk in analyze:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            full_content += delta.content

    return json.loads(full_content)
