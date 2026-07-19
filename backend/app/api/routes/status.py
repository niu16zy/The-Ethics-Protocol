from __future__ import annotations

from fastapi import APIRouter

from backend.app.api import dependencies
from backend.app.schemas.status import LLMStatus

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/status", response_model=LLMStatus)
def get_llm_status() -> LLMStatus:
    current_settings = dependencies.settings()
    client = dependencies.llm_client()
    if current_settings.llm_provider == "fox":
        model = current_settings.fox_model
        api_key_configured = bool(current_settings.fox_api_key)
    else:
        model = current_settings.groq_model
        api_key_configured = bool(current_settings.groq_api_key)
    return LLMStatus(
        provider=current_settings.llm_provider,
        model=model,
        timeout_seconds=current_settings.groq_timeout_seconds,
        max_attempts=current_settings.llm_max_attempts,
        max_output_tokens=current_settings.groq_max_output_tokens,
        api_key_configured=api_key_configured,
        client_configured=client is not None,
        using_rules_fallback=client is None,
    )
