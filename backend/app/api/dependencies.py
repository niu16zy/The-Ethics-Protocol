from __future__ import annotations

from backend.app.core.config import Settings, get_settings
from backend.app.repositories.app_repository import AppRepository
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.services.conversation_context_service import ConversationContextService
from backend.app.services.llm_client import LLMClient, create_llm_client
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.meter_service import MeterService
from backend.app.services.orchestrator_service import DebateOrchestrator
from backend.app.services.persona_service import PersonaService
from backend.app.services.retrieval_service import RetrievalService


PERSONA_MAX_OUTPUT_TOKENS = 300


def settings() -> Settings:
    return get_settings()


def app_repository() -> AppRepository:
    repository = AppRepository(settings().app_db_path)
    repository.initialize()
    return repository


def knowledge_repository() -> KnowledgeRepository:
    return KnowledgeRepository(settings().knowledge_db_path)


def retrieval_service() -> RetrievalService:
    current_settings = settings()
    return RetrievalService(
        knowledge_repository(),
        default_top_k=current_settings.default_top_k,
    )


def llm_client(max_output_tokens: int | None = None) -> LLMClient | None:
    current_settings = settings()
    return create_llm_client(
        provider=current_settings.llm_provider,
        groq_api_key=current_settings.groq_api_key,
        groq_model=current_settings.groq_model,
        fox_api_key=current_settings.fox_api_key,
        fox_model=current_settings.fox_model,
        fox_base_url=current_settings.fox_base_url,
        fox_reasoning_effort=current_settings.fox_reasoning_effort,
        fox_disable_response_storage=current_settings.fox_disable_response_storage,
        timeout_seconds=current_settings.groq_timeout_seconds,
        max_output_tokens=max_output_tokens or current_settings.groq_max_output_tokens,
    )


def orchestrator() -> DebateOrchestrator:
    current_settings = settings()
    client = llm_client()
    persona_client = llm_client(
        max_output_tokens=min(
            current_settings.groq_max_output_tokens,
            PERSONA_MAX_OUTPUT_TOKENS,
        )
    )
    return DebateOrchestrator(
        app_repository=app_repository(),
        retrieval_service=retrieval_service(),
        evaluation_service=EvaluationService(
            llm_client=client,
            max_attempts=current_settings.llm_max_attempts,
        ),
        persona_service=PersonaService(
            llm_client=persona_client,
            max_attempts=current_settings.llm_max_attempts,
        ),
        meter_service=MeterService(),
        conversation_context_service=ConversationContextService(),
    )
