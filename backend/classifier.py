import asyncio
import json
import time
import os
from groq import AsyncGroq

CLASSIFIER_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

SYSTEM_PROMPT = """Tu es un assistant spécialisé dans l'analyse de réunions et d'enregistrements audio.
Réponds UNIQUEMENT avec un objet JSON valide contenant exactement ces champs :
- "resume": string — résumé bref en 2-3 phrases
- "actions_decisions": array de strings — chaque action ou décision prise (liste vide si aucune)
- "taches_assignees": array de strings — chaque tâche assignée avec le responsable si mentionné (liste vide si aucune)"""

USER_PROMPT = """Analyse cette transcription et retourne le JSON demandé.

Transcription :
{transcript}"""

_client: AsyncGroq | None = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def _to_str_list(items: list) -> list[str]:
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            # LLM sometimes returns {"tache": "...", "responsable": "..."} etc.
            parts = [str(v) for v in item.values() if v]
            result.append(" — ".join(parts))
    return result


def _parse_response(content: str) -> dict:
    content = content.strip()
    # Strip markdown code fences if present
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(content)


async def _classify_one(transcript: str, model: str) -> dict:
    start = time.monotonic()
    client = _get_client()

    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(transcript=transcript)},
        ],
        temperature=0.2,
        max_tokens=1024,
        timeout=25,
    )
    # JSON mode is supported on all current Groq models
    try:
        kwargs["response_format"] = {"type": "json_object"}
        response = await client.chat.completions.create(**kwargs)
    except Exception:
        kwargs.pop("response_format", None)
        response = await client.chat.completions.create(**kwargs)

    raw = response.choices[0].message.content
    duration_ms = int((time.monotonic() - start) * 1000)

    try:
        parsed = _parse_response(raw)
    except json.JSONDecodeError:
        parsed = {"resume": raw, "actions_decisions": [], "taches_assignees": []}

    return {
        "model": model,
        "resume": parsed.get("resume", ""),
        "actions_decisions": _to_str_list(parsed.get("actions_decisions", [])),
        "taches_assignees": _to_str_list(parsed.get("taches_assignees", [])),
        "duration_ms": duration_ms,
    }


async def run_all_classifiers(transcript: str) -> list[dict]:
    tasks = [
        asyncio.wait_for(_classify_one(transcript, model), timeout=30)
        for model in CLASSIFIER_MODELS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    good = [r for r in results if not isinstance(r, Exception)]
    if not good:
        raise RuntimeError("All classifiers failed or timed out")
    return good
