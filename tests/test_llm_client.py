from __future__ import annotations

import json

import pytest

from backend.app.services.llm_client import (
    FoxResponsesClient,
    GroqChatCompletionsClient,
    LLMClientError,
)


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


def test_fox_generate_sends_responses_payload(monkeypatch):
    captured_payload: dict[str, object] = {}
    captured_url = ""
    captured_authorization = ""

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def __iter__(self):
            yield b"event: response.output_text.delta\n"
            yield b'data: {"type":"response.output_text.delta","delta":"{\\"ok\\":"}\n'
            yield b'data: {"type":"response.output_text.delta","delta":" true}"}\n'
            yield b"data: [DONE]\n"

    def fake_urlopen(request, timeout):
        nonlocal captured_payload
        nonlocal captured_url
        nonlocal captured_authorization
        captured_payload = json.loads(request.data.decode("utf-8"))
        captured_url = request.full_url
        captured_authorization = request.get_header("Authorization")
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = FoxResponsesClient(
        api_key="fox-key",
        model="gpt-5.5",
        base_url="https://code.newcli.com/codex/v1/",
        max_output_tokens=300,
        reasoning_effort="high",
        disable_response_storage=True,
    )

    assert (
        client.generate_text(
            "Return JSON.",
            temperature=0.7,
            response_mime_type="application/json",
        )
        == "{\"ok\": true}"
    )
    assert captured_url == "https://code.newcli.com/codex/v1/responses"
    assert captured_authorization == "Bearer fox-key"
    assert captured_payload["model"] == "gpt-5.5"
    assert captured_payload["input"] == [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": "Return JSON."}],
        }
    ]
    assert captured_payload["max_output_tokens"] == 300
    assert captured_payload["store"] is False
    assert captured_payload["stream"] is True
    assert captured_payload["reasoning"] == {"effort": "high"}
    assert "text" not in captured_payload
    assert "temperature" not in captured_payload
