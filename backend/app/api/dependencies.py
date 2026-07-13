from __future__ import annotations

from backend.app.core.config import Settings, get_settings
from backend.app.repositories.app_repository import AppRepository
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.services.conversation_context_service import ConversationContextService
from backend.app.services.dialogue_brief_service import DialogueBriefService
from backend.app.services.llm_client import LLMClient, create_llm_client
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.meter_service import MeterService
from backend.app.services.orchestrator_service import DebateOrchestrator
from backend.app.services.persona_service import PersonaService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.turn_router_service import TurnRouterService


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


def llm_client() -> LLMClient | None:
    current_settings = settings()
    return create_llm_client(
        provider=current_settings.llm_provider,
        groq_api_key=current_settings.groq_api_key,
        groq_model=current_settings.groq_model,
        timeout_seconds=current_settings.groq_timeout_seconds,
        max_output_tokens=current_settings.groq_max_output_tokens,
    )


def orchestrator() -> DebateOrchestrator:
    client = llm_client()
    return DebateOrchestrator(
        app_repository=app_repository(),
        retrieval_service=retrieval_service(),
        evaluation_service=EvaluationService(
            llm_client=client,
            max_attempts=settings().llm_max_attempts,
        ),
        persona_service=PersonaService(llm_client=client),
        meter_service=MeterService(),
        conversation_context_service=ConversationContextService(),
        turn_router_service=TurnRouterService(),
        dialogue_brief_service=DialogueBriefService(),
    )
