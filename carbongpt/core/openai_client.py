"""
Unified AI client for CarbonGPT.

Text generation goes through Anthropic's Claude API. OpenAI is kept only for
embeddings (Anthropic doesn't offer an embeddings endpoint) — see
get_openai_api_key() below, used by callers that still talk to OpenAI's
embeddings endpoint directly (carbongpt/repository/ingestion.py).

The module and its main function keep their historical name (`call_openai`,
`openai_client.py`) so the ~15 existing call sites across ai_writer.py and
calculation_engine.py don't need to change — only what happens inside this
file changed. See docs/DECISIONS.md for context (Anthropic switch, 2026).

Each key is read independently and fails loudly, never silently, when the
capability that needs it is used without it being set:
  - ANTHROPIC_API_KEY — required by call_openai() (text generation)
  - OPENAI_API_KEY    — required by get_openai_api_key() (embeddings)
"""

import json
import logging
import os

import requests as http_client

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"

# Single source of truth for Claude model names. Every other module that
# needs a model name imports one of these constants instead of hardcoding
# "claude-sonnet-5"/"claude-opus-5" — changing model generation means
# editing these four lines, not every caller.
DEFAULT_MODEL = os.getenv("CARBONGPT_AI_MODEL", "claude-sonnet-5")
UPGRADE_MODEL = os.getenv("CARBONGPT_UPGRADE_MODEL", "claude-opus-5")
PARSE_MODEL = os.getenv("CARBONGPT_PARSE_MODEL", "claude-opus-5")
STRUCTURE_MODEL = os.getenv("CARBONGPT_STRUCTURE_MODEL", "claude-sonnet-5")

_DEFAULT_MODEL = DEFAULT_MODEL


def _get_anthropic_api_key() -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Text generation (call_openai) requires it — set it in your .env "
            "file or environment before starting the app. See CLAUDE.md §5."
        )
    return api_key


def get_openai_api_key() -> str:
    """OpenAI is only used for embeddings now (Anthropic has no embeddings
    endpoint). Callers that need an embedding — currently
    carbongpt/repository/ingestion.py:create_embeddings — should call this
    rather than reading os.environ directly, so the failure message stays
    consistent. Fails loudly if unset; never falls back silently."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Embeddings require it (Anthropic has no embeddings endpoint) — "
            "set it in your .env file or environment. See CLAUDE.md §5."
        )
    return api_key


def _resolve_model(model_override: str | None) -> str:
    """Guards against stale OpenAI model names (e.g. "gpt-4o-mini",
    "gpt-4o") leaking in from callers whose own CARBONGPT_AI_MODEL /
    CARBONGPT_UPGRADE_MODEL fallbacks still default to OpenAI models —
    ai_writer.py in particular. Anthropic would just reject those with a
    404; substituting the Claude default and logging a warning is more
    useful than a confusing API error. A genuine Claude model name passed
    as model_override is always respected as-is."""
    model = model_override or _DEFAULT_MODEL
    if model.startswith("gpt-"):
        logger.warning(
            "call_openai received OpenAI model name %r (likely a stale "
            "CARBONGPT_AI_MODEL/CARBONGPT_UPGRADE_MODEL default from a "
            "caller not yet updated for the Anthropic switch) — using %r "
            "instead.", model, _DEFAULT_MODEL,
        )
        return _DEFAULT_MODEL
    return model


def _to_anthropic_tool(response_format: dict) -> dict:
    """Converts an OpenAI-style response_format
    ({"type": "json_schema", "json_schema": {"name", "schema"}}) into an
    Anthropic tool definition. Structured output on Anthropic is done via a
    forced tool call, not a response_format parameter."""
    json_schema = response_format.get("json_schema", {})
    return {
        "name": json_schema.get("name", "structured_output"),
        "description": "Return the result matching this schema.",
        "input_schema": json_schema.get("schema", {}),
    }


def call_openai(
    system_prompt: str,
    user_prompt: str,
    response_format=None,
    max_tokens: int = 4000,
    temperature: float = 0.4,
    model_override: str | None = None,
) -> str:
    """
    Send a message to Claude (Anthropic). Name and signature kept for
    backward compatibility with existing callers.

    Parameters
    ----------
    system_prompt    : System message content.
    user_prompt      : User message content.
    response_format  : Optional OpenAI-style json_schema dict. When given,
                       structured output is produced via a forced Anthropic
                       tool call, and the returned string is the JSON-encoded
                       tool input (same contract as before: callers already
                       do json.loads(result) on it).
    max_tokens       : Maximum tokens to generate. Default 4000.
    temperature      : Sampling temperature. Use 0.4 for narrative writing,
                       0.1 for deterministic structured extraction.
    model_override   : Override the default model for this call only. A
                       stale OpenAI model name is detected and replaced —
                       see _resolve_model().

    Returns
    -------
    str — the response text (or, with response_format, a JSON string).
    """
    api_key = _get_anthropic_api_key()
    model = _resolve_model(model_override)

    payload = {
        "model": model,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    if response_format:
        tool = _to_anthropic_tool(response_format)
        payload["tools"] = [tool]
        payload["tool_choice"] = {"type": "tool", "name": tool["name"]}

    resp = http_client.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()

    if response_format:
        for block in data.get("content", []):
            if block.get("type") == "tool_use":
                return json.dumps(block["input"])
        raise ValueError("Anthropic response contained no tool_use block for the requested response_format")

    text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    return "".join(text_blocks)


def _openai_tool_to_anthropic(tool: dict) -> dict:
    fn = tool.get("function", tool)
    return {"name": fn["name"], "description": fn.get("description", ""), "input_schema": fn.get("parameters", {})}


def _to_anthropic_messages(messages: list[dict]) -> list[dict]:
    """Translates OpenAI-shaped chat messages (role: system/user/assistant/tool,
    with tool_calls / tool_call_id) into Anthropic's format. `system` messages
    are dropped here — call_with_tools() takes system_prompt separately."""
    result = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        if role == "tool":
            result.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m.get("content", "")},
            ]})
        elif role == "assistant" and m.get("tool_calls"):
            blocks = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for tc in m["tool_calls"]:
                args = tc["function"].get("arguments", "{}")
                if isinstance(args, str):
                    args = json.loads(args) if args else {}
                blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"], "input": args})
            result.append({"role": "assistant", "content": blocks})
        else:
            result.append({"role": role, "content": m.get("content", "")})
    return result


def call_with_tools(
    system_prompt: str,
    messages: list[dict],
    tools: list[dict],
    max_tokens: int = 2000,
    temperature: float = 0.3,
    model_override: str | None = None,
) -> dict:
    """
    Agentic tool-calling call: the model decides whether to invoke a tool or
    just reply conversationally (Anthropic tool_choice="auto"). Used by
    copilot.py — the one caller in this codebase where the model needs to
    pick actions, not just produce structured output.

    Takes and returns OpenAI-shaped data (messages, tools, and the response)
    so callers written against the OpenAI chat-completions shape don't need
    to change — only this function knows about Anthropic's wire format.

    Parameters
    ----------
    system_prompt  : System message content.
    messages       : OpenAI-style message list (role: user/assistant/tool).
    tools          : OpenAI-style tool definitions
                     ([{"type": "function", "function": {name, description, parameters}}]).
    model_override : Same stale-name guard as call_openai() — see _resolve_model().

    Returns
    -------
    dict shaped like an OpenAI choice: {"finish_reason": "tool_calls" | "stop",
    "message": {"role": "assistant", "content": str | None,
                "tool_calls": [{"id", "type": "function", "function": {"name", "arguments"}}] | None}}
    """
    api_key = _get_anthropic_api_key()
    model = _resolve_model(model_override)

    payload = {
        "model": model,
        "system": system_prompt,
        "messages": _to_anthropic_messages(messages),
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        payload["tools"] = [_openai_tool_to_anthropic(t) for t in tools]
        payload["tool_choice"] = {"type": "auto"}

    resp = http_client.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()

    content_blocks = data.get("content", [])
    text = "".join(b["text"] for b in content_blocks if b.get("type") == "text")
    tool_use_blocks = [b for b in content_blocks if b.get("type") == "tool_use"]

    tool_calls = [
        {"id": b["id"], "type": "function",
         "function": {"name": b["name"], "arguments": json.dumps(b.get("input", {}))}}
        for b in tool_use_blocks
    ]

    return {
        "finish_reason": "tool_calls" if tool_calls else "stop",
        "message": {"role": "assistant", "content": text or None, "tool_calls": tool_calls or None},
    }
