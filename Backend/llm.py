import json
from groq import Groq

client = Groq()

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