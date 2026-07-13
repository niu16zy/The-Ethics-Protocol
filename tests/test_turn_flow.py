from __future__ import annotations

import json
from pathlib import Path

from backend.app.repositories.app_repository import AppRepository
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.user import UserCreate
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.meter_service import MeterService
from backend.app.services.orchestrator_service import DebateOrchestrator
from backend.app.services.persona_service import PersonaService
from backend.app.services.retrieval_service import RetrievalService


def test_debate_turn_happy_path_persists_traceable_turn(tmp_path):
    app_repository = AppRepository(tmp_path / "logic_fortress_app.db")
    app_repository.initialize()
    user = app_repository.create_user(
        UserCreate(username="auditor2", display_name="Trace Auditor")
    )
    session = app_repository.create_session(user.id, current_level=1, initial_meter=100)
    knowledge_db = Path(__file__).resolve().parents[1] / "course_content.db"
    orchestrator = DebateOrchestrator(
        app_repository=app_repository,
        retrieval_service=RetrievalService(KnowledgeRepository(knowledge_db), default_top_k=3),
        evaluation_service=EvaluationService(),
        persona_service=PersonaService(),
        meter_service=MeterService(),
    )

    response = orchestrator.submit_turn(
        session.id,
        "A hiring AI can be unfair if biased training data discriminates against applicants.",
    )
    rows = app_repository.fetch_turns(session.id)

    assert response.turn_index == 1
    assert response.retrieved_refs
    assert response.meter_after <= response.meter_before
    assert response.evaluator_source == "rules"
    assert response.persona_source == "rules"
    assert len(rows) == 1
    persisted_refs = json.loads(rows[0]["retrieved_refs"])
    persisted_eval = json.loads(rows[0]["evaluator_json"])
    assert persisted_refs[0]["document_id"]
    assert persisted_eval["verdict"] in {
        "strong",
        "partial",
        "weak",
        "unsupported",
        "off_topic",
    }
