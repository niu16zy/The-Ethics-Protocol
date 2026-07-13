from __future__ import annotations

from pydantic import BaseModel


class LLMStatus(BaseModel):
    provider: str
    model: str
    timeout_seconds: int
    max_attempts: int
    max_output_tokens: int
    api_key_configured: bool
    client_configured: bool
    using_rules_fallback: bool
