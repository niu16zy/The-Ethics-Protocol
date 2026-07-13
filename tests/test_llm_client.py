from __future__ import annotations

import json

import pytest

from backend.app.services.llm_client import GroqChatCompletionsClient, LLMClientError


def test_groq_generate_timeout_is_wrapped(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise TimeoutError("read operation timed out")

    monkeypatch.setattr("urllib.request.urlopen", raise_timeout)
    client = GroqChatCompletionsClient(api_key="fake-key", timeout_seconds=1)

    with pytest.raises(LLMClientError, match="timed out"):
        client.generate_text("hello", temperature=0.1)


def test_groq_stream_timeout_is_wrapped(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise TimeoutError("read operation timed out")

    monkeypatch.setattr("urllib.request.urlopen", raise_timeout)
    client = GroqChatCompletionsClient(api_key="fake-key", timeout_seconds=1)

    with pytest.raises(LLMClientError, match="timed out"):
        list(client.stream_text("hello", temperature=0.1))


def test_groq_generate_sends_max_tokens(monkeypatch):
    captured_payload: dict[str, object] = {}
    captured_user_agent = ""

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {"choices": [{"message": {"content": "{\"ok\": true}"}}]}
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        nonlocal captured_payload
        nonlocal captured_user_agent
        captured_payload = json.loads(request.data.decode("utf-8"))
        captured_user_agent = request.get_header("User-agent")
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = GroqChatCompletionsClient(
        api_key="fake-key",
        model="llama-3.3-70b-versatile",
        max_output_tokens=512,
    )

    assert client.generate_text("Return JSON.", temperature=0.0) == "{\"ok\": true}"
    assert captured_payload["max_tokens"] == 512
    assert captured_payload["model"] == "llama-3.3-70b-versatile"
    assert captured_user_agent == "logic-fortress/0.1"
