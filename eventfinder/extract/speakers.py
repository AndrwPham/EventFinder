import json
import os
import re
from typing import List

import requests

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.getenv("EVENTFINDER_LLM_MODEL", "gpt-4o")
ENABLE_LLM_SPEAKERS = 1
LOG_LLM_SPEAKERS = 0
LLM_SPEAKER_MIN_CHARS = 300
LLM_SPEAKER_MAX_CHARS = 2000


def infer_speakers_with_llm(overview: str) -> List[str]:
    if not ENABLE_LLM_SPEAKERS:
        return []
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []

    cleaned = overview.strip()
    if len(cleaned) > LLM_SPEAKER_MAX_CHARS:
        cleaned = cleaned[:LLM_SPEAKER_MAX_CHARS]
    if len(cleaned) < LLM_SPEAKER_MIN_CHARS:
        return []

    prompt = (
        "Extract speaker names from the event overview. "
        "Return JSON only: {\"speakers\": [\"Name\", ...]}. "
        "If no speakers are mentioned, return {\"speakers\": []}. "
        "Do not guess."
    )
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You extract event speakers."},
            {"role": "user", "content": f"{prompt}\n\nOverview:\n{cleaned}"},
        ],
        "temperature": 0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
    }

    if LOG_LLM_SPEAKERS:
        print("LLM overview:")
        print(cleaned)

    try:
        response = requests.post(
            OPENAI_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return []

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if LOG_LLM_SPEAKERS:
        print("LLM response:")
        print(content)
    return _parse_speakers_response(content)


def _parse_speakers_response(content: str) -> List[str]:
    if not content:
        return []
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return _split_speaker_fallback(content)
    if isinstance(parsed, list):
        return [str(item) for item in parsed if str(item).strip()]
    if isinstance(parsed, dict):
        for key in ("speakers", "speaker", "names"):
            value = parsed.get(key)
            if isinstance(value, list):
                return [str(item) for item in value if str(item).strip()]
            if isinstance(value, str) and value.strip():
                return [value.strip()]
    if isinstance(parsed, str) and parsed.strip():
        return [parsed.strip()]
    return []


def _split_speaker_fallback(content: str) -> List[str]:
    if not content:
        return []
    parts = re.split(r"[,\n;]+", content)
    return [part.strip() for part in parts if part.strip()]
