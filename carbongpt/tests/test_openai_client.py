"""
Tests for carbongpt.core.openai_client (Anthropic-backed text generation,
OpenAI kept only for embeddings). No network calls — HTTP is monkeypatched.
"""
import json

import pytest


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class TestApiKeyGuards:
    def test_call_openai_raises_explicitly_without_anthropic_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from carbongpt.core.openai_client import call_openai
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            call_openai("system", "user")

    def test_get_openai_api_key_raises_explicitly_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from carbongpt.core.openai_client import get_openai_api_key
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            get_openai_api_key()

    def test_get_openai_api_key_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        from carbongpt.core.openai_client import get_openai_api_key
        assert get_openai_api_key() == "sk-test-123"


class TestResolveModel:
    def test_stale_gpt_model_name_is_replaced(self):
        from carbongpt.core.openai_client import _resolve_model, _DEFAULT_MODEL
        assert _resolve_model("gpt-4o-mini") == _DEFAULT_MODEL
        assert _resolve_model("gpt-4o") == _DEFAULT_MODEL

    def test_claude_model_override_is_respected(self):
        from carbongpt.core.openai_client import _resolve_model
        assert _resolve_model("claude-opus-5") == "claude-opus-5"

    def test_no_override_uses_default(self):
        from carbongpt.core.openai_client import _resolve_model, _DEFAULT_MODEL
        assert _resolve_model(None) == _DEFAULT_MODEL

    def test_default_model_is_not_openai(self):
        from carbongpt.core.openai_client import _DEFAULT_MODEL
        assert not _DEFAULT_MODEL.startswith("gpt-")


class TestToAnthropicTool:
    def test_converts_openai_json_schema_to_anthropic_tool(self):
        from carbongpt.core.openai_client import _to_anthropic_tool
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": "emission_calculation", "schema": {"type": "object", "properties": {}}},
        }
        tool = _to_anthropic_tool(response_format)
        assert tool["name"] == "emission_calculation"
        assert tool["input_schema"] == {"type": "object", "properties": {}}


class TestCallOpenAiPlainText:
    def test_returns_concatenated_text_blocks(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def fake_post(url, headers=None, json=None, timeout=None):
            assert url == "https://api.anthropic.com/v1/messages"
            assert headers["x-api-key"] == "test-key"
            assert json["system"] == "sys"
            return _FakeResponse({"content": [{"type": "text", "text": "hello world"}]})

        import carbongpt.core.openai_client as mod
        monkeypatch.setattr(mod.http_client, "post", fake_post)
        result = mod.call_openai("sys", "user prompt")
        assert result == "hello world"

    def test_stale_openai_model_override_does_not_reach_anthropic(self, monkeypatch, caplog):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["model"] = json["model"]
            return _FakeResponse({"content": [{"type": "text", "text": "ok"}]})

        import carbongpt.core.openai_client as mod
        monkeypatch.setattr(mod.http_client, "post", fake_post)
        mod.call_openai("sys", "user", model_override="gpt-4o-mini")
        assert not captured["model"].startswith("gpt-")


class TestCallOpenAiStructuredOutput:
    def test_response_format_uses_forced_tool_and_returns_json_string(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def fake_post(url, headers=None, json=None, timeout=None):
            assert json["tool_choice"] == {"type": "tool", "name": "emission_calculation"}
            return _FakeResponse({
                "content": [
                    {"type": "tool_use", "id": "t1", "name": "emission_calculation",
                     "input": {"total_er": 123.4}},
                ]
            })

        import carbongpt.core.openai_client as mod
        monkeypatch.setattr(mod.http_client, "post", fake_post)
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": "emission_calculation", "schema": {"type": "object"}},
        }
        result = mod.call_openai("sys", "user", response_format=response_format)
        assert json.loads(result) == {"total_er": 123.4}

    def test_missing_tool_use_block_raises(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def fake_post(url, headers=None, json=None, timeout=None):
            return _FakeResponse({"content": [{"type": "text", "text": "I refuse to use the tool"}]})

        import carbongpt.core.openai_client as mod
        monkeypatch.setattr(mod.http_client, "post", fake_post)
        response_format = {"type": "json_schema", "json_schema": {"name": "x", "schema": {}}}
        with pytest.raises(ValueError, match="tool_use"):
            mod.call_openai("sys", "user", response_format=response_format)
