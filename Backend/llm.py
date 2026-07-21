import json
from together import Together

client = Together()

with open("agent_context.txt", "r") as f:
    context = f.read()

def generate_report(transcript):
    analyze = client.chat.completions.create(
        model="Qwen/Qwen3.7-Max",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": transcript}
        ],
        temperature=0,
        max_tokens=4096,
        stream=True,
        response_format={"type": "json_object"}
    )

    full_content = ""
    for chunk in analyze:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            full_content += delta.content

    return json.loads(full_content)
