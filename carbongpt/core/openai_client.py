"""
Unified OpenAI HTTP client for CarbonGPT.

Single point of entry for all GPT calls across ai_writer, calculation_engine,
and any future module. Eliminates the two separate _call_openai implementations
that previously lived in ai_writer.py and calculation_engine.py.
"""

import logging
import os

import requests as http_client

logger = logging.getLogger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
_DEFAULT_MODEL = os.getenv("CARBONGPT_AI_MODEL", "gpt-4o-mini")


def _get_api_key() -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    return api_key


def call_openai(
    system_prompt: str,
    user_prompt: str,
    response_format=None,
    max_tokens: int = 4000,
    temperature: float = 0.4,
    model_override: str | None = None,
) -> str:
    """
    Send a chat-completions request to the OpenAI API.

    Parameters
    ----------
    system_prompt    : System message content.
    user_prompt      : User message content.
    response_format  : Optional structured-output schema dict (e.g. JSON schema).
    max_tokens       : Maximum tokens to generate. Default 4000.
    temperature      : Sampling temperature. Use 0.4 for narrative writing,
                       0.1 for deterministic structured extraction.
    model_override   : Override the default model for this call only.

    Returns
    -------
    str — raw text content of the first response choice.
    """
    api_key = _get_api_key()
    model = model_override or _DEFAULT_MODEL
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format:
        payload["response_format"] = response_format

    resp = http_client.post(
        OPENAI_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
