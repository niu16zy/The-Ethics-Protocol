from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from collections.abc import Iterator
from typing import Protocol


class LLMClient(Protocol):
    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float,
        response_mime_type: str | None = None,
    ) -> str:
        """Generate text from a provider without exposing provider details to services."""

    def stream_text(
        self,
        prompt: str,
        *,
        temperature: float,
        response_mime_type: str | None = None,
    ) -> Iterator[str]:
        """Stream generated text chunks from a provider."""


class LLMClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class GroqChatCompletionsClient:
    api_key: str
    model: str = "llama-3.3-70b-versatile"
    endpoint_url: str = "https://api.groq.com/openai/v1/chat/completions"
    timeout_seconds: int = 30
    max_output_tokens: int = 700
    user_agent: str = "logic-fortress/0.1"

    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float,
        response_mime_type: str | None = None,
    ) -> str:
        generation_config: dict[str, object] = {"temperature": temperature}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_output_tokens,
            **generation_config,
        }
        if response_mime_type == "application/json":
            payload["response_format"] = {"type": "json_object"}

        request = urllib.request.Request(
            url=self.endpoint_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._request_headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMClientError(f"Groq request failed with HTTP {exc.code}: {detail}") from exc
        except TimeoutError as exc:
            raise LLMClientError("Groq request timed out while waiting for a response.") from exc
        except socket.timeout as exc:
            raise LLMClientError("Groq request timed out while waiting for a response.") from exc
        except urllib.error.URLError as exc:
            raise LLMClientError(f"Groq request failed: {exc.reason}") from exc

        try:
            data = json.loads(response_body)
            content = data["choices"][0]["message"]["content"]
            return str(content).strip()
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LLMClientError("Groq response did not contain generated text.") from exc

    def stream_text(
        self,
        prompt: str,
        *,
        temperature: float,
        response_mime_type: str | None = None,
    ) -> Iterator[str]:
        generation_config: dict[str, object] = {"temperature": temperature}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_output_tokens,
            "stream": True,
            **generation_config,
        }
        if response_mime_type == "application/json":
            payload["response_format"] = {"type": "json_object"}

        request = urllib.request.Request(
            url=self.endpoint_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._request_headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    event_payload = line.removeprefix("data:").strip()
                    if event_payload == "[DONE]":
                        continue
                    chunk = self._text_from_stream_event(event_payload)
                    if chunk:
                        yield chunk
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMClientError(f"Groq stream failed with HTTP {exc.code}: {detail}") from exc
        except TimeoutError as exc:
            raise LLMClientError("Groq stream timed out while waiting for a response.") from exc
        except socket.timeout as exc:
            raise LLMClientError("Groq stream timed out while waiting for a response.") from exc
        except urllib.error.URLError as exc:
            raise LLMClientError(f"Groq stream failed: {exc.reason}") from exc

    def _text_from_stream_event(self, payload: str) -> str:
        try:
            data = json.loads(payload)
            delta = data["choices"][0].get("delta", {})
            content = delta.get("content", "")
            return str(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LLMClientError("Groq stream response did not contain generated text.") from exc

    def _request_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": self.user_agent,
        }


@dataclass(frozen=True)
class FoxResponsesClient:
    api_key: str
    model: str = "gpt-5.5"
    base_url: str = "https://code.newcli.com/codex/v1"
    timeout_seconds: int = 30
    max_output_tokens: int = 700
    reasoning_effort: str = "high"
    disable_response_storage: bool = True
    user_agent: str = "logic-fortress/0.1"

    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float,
        response_mime_type: str | None = None,
    ) -> str:
        payload: dict[str, object] = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": self.max_output_tokens,
            "store": not self.disable_response_storage,
        }
        if self.reasoning_effort:
            payload["reasoning"] = {"effort": self.reasoning_effort}
        if response_mime_type == "application/json":
            payload["text"] = {"format": {"type": "json_object"}}

        request = urllib.request.Request(
            url=self._responses_endpoint(),
            data=json.dumps(payload).encode("utf-8"),
            headers=self._request_headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMClientError(f"Fox request failed with HTTP {exc.code}: {detail}") from exc
        except TimeoutError as exc:
            raise LLMClientError("Fox request timed out while waiting for a response.") from exc
        except socket.timeout as exc:
            raise LLMClientError("Fox request timed out while waiting for a response.") from exc
        except urllib.error.URLError as exc:
            raise LLMClientError(f"Fox request failed: {exc.reason}") from exc

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise LLMClientError("Fox response was not valid JSON.") from exc
        content = self._text_from_response(data)
        if not content:
            raise LLMClientError("Fox response did not contain generated text.")
        return content.strip()

    def stream_text(
        self,
        prompt: str,
        *,
        temperature: float,
        response_mime_type: str | None = None,
    ) -> Iterator[str]:
        yield self.generate_text(
            prompt,
            temperature=temperature,
            response_mime_type=response_mime_type,
        )

    def _responses_endpoint(self) -> str:
        return f"{self.base_url.rstrip('/')}/responses"

    def _request_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": self.user_agent,
        }

    def _text_from_response(self, data: dict[str, object]) -> str:
        output_text = data.get("output_text")
        if isinstance(output_text, str):
            return output_text

        chunks: list[str] = []
        output = data.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    text = part.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
        return "".join(chunks)


def create_llm_client(
    *,
    provider: str,
    groq_api_key: str | None,
    groq_model: str,
    fox_api_key: str | None = None,
    fox_model: str = "gpt-5.5",
    fox_base_url: str = "https://code.newcli.com/codex/v1",
    fox_reasoning_effort: str = "high",
    fox_disable_response_storage: bool = True,
    timeout_seconds: int = 90,
    max_output_tokens: int = 700,
) -> LLMClient | None:
    if provider == "groq" and groq_api_key:
        return GroqChatCompletionsClient(
            api_key=groq_api_key,
            model=groq_model,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
    if provider == "fox" and fox_api_key:
        return FoxResponsesClient(
            api_key=fox_api_key,
            model=fox_model,
            base_url=fox_base_url,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
            reasoning_effort=fox_reasoning_effort,
            disable_response_storage=fox_disable_response_storage,
        )
    return None
