from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api import dependencies
from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.repositories.app_repository import AppRepository
from backend.app.schemas.evaluator import EvaluatorResult, EvidenceRef
from backend.app.services.llm_client import LLMClientError
from backend.app.services.persona_service import PersonaService


def test_stream_turn_endpoint_emits_events_and_persists_once(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    app_db_path = tmp_path / "logic_fortress_app.db"

    def test_settings() -> Settings:
        return Settings(
            project_root=project_root,
            knowledge_db_path=project_root / "course_content.db",
            app_db_path=app_db_path,
            llm_provider="rules",
            groq_api_key=None,
            groq_model="llama-3.3-70b-versatile",
            groq_timeout_seconds=90,
            llm_max_attempts=2,
        )

    dependencies.settings = test_settings
    app = create_app()
    client = TestClient(app)

    user_response = client.post(
        "/api/users",
        json={"username": "streamuser", "display_name": "Stream User"},
    )
    session_response = client.post(
        "/api/sessions",
        json={"user_id": user_response.json()["id"]},
    )
    session_id = session_response.json()["id"]

    with client.stream(
        "POST",
        f"/api/sessions/{session_id}/turns/stream",
        json={
            "player_input": "Fairness matters because biased AI hiring data can discriminate."
        },
    ) as response:
        assert response.status_code == 200
        events = [json.loads(line) for line in response.iter_lines() if line]

    event_names = [event["event"] for event in events]
    assert event_names[:4] == ["phase", "phase", "evaluator_complete", "phase"]
    assert "persona_delta" in event_names
    assert event_names[-1] == "complete"
    assert events[0]["phase"] == "retrieving"
    assert events[1]["phase"] == "evaluating"
    assert events[3]["phase"] == "persona"
    assert events[-1]["turn"]["persona_source"] == "rules"

    turns = AppRepository(app_db_path).fetch_turns(session_id)
    assert len(turns) == 1
    assert turns[0]["npc_response"] == events[-1]["turn"]["npc_response"]


def test_persona_streaming_failure_falls_back_to_rule_chunks():
    class FailingGenerateClient:
        def generate_text(
            self,
            prompt: str,
            *,
            temperature: float,
            response_mime_type: str | None = None,
        ) -> str:
            raise LLMClientError("persona unavailable")

    evaluator = EvaluatorResult(
        match_score=0.0,
        score_delta=0,
        verdict="unsupported",
        identified_principles=[],
        misconceptions_addressed=[],
        missing_points=["Clarify the argument."],
        evidence_refs=[],
        reasoning_summary="No evidence.",
        persona_instruction="Ask for clarification.",
        confidence=0.0,
    )
    service = PersonaService(llm_client=FailingGenerateClient())

    text = "".join(service.stream_dialogue(evaluator, meter_after=100))

    assert service.last_source == "fallback"
    assert "clarify" in text.lower()


def test_persona_streaming_uses_llm_json_then_local_chunks_and_omits_evidence_refs():
    class CapturingGenerateClient:
        def __init__(self) -> None:
            self.prompt = ""

        def generate_text(
            self,
            prompt: str,
            *,
            temperature: float,
            response_mime_type: str | None = None,
        ) -> str:
            self.prompt = prompt
            return json.dumps(
                {
                        "npc_response": (
                            "You found a real pressure point in the rollout, and I cannot bury it under "
                            "efficiency language. The fairness issue still needs accountability, but the "
                            "board story is no longer clean, simple, or safe for me to wave through "
                            "without exposure."
                        ),
                    "npc_state": "defensive",
                    "follow_up_prompt": "Clarify the accountability point.",
                }
            )

    evaluator = EvaluatorResult(
        match_score=0.6,
        score_delta=-8,
        verdict="partial",
        identified_principles=["fairness"],
        misconceptions_addressed=[],
        missing_points=["Explain accountability."],
        evidence_refs=[
            EvidenceRef(
                document_id=108,
                topic="Fairness",
                excerpt="This long course evidence excerpt should not be sent to Persona streaming.",
            )
        ],
        reasoning_summary="The claim is partly grounded.",
        persona_instruction="Press for a sharper explanation.",
        confidence=0.61,
    )
    client = CapturingGenerateClient()
    expected = (
        "You found a real pressure point in the rollout, and I cannot bury it under "
        "efficiency language. The fairness issue still needs accountability, but the "
        "board story is no longer clean, simple, or safe for me to wave through "
        "without exposure."
    )

    service = PersonaService(llm_client=client)
    assert "".join(service.stream_dialogue(evaluator, 92)) == expected
    assert service.last_source == "llm"
    assert "evidence_refs" not in client.prompt
    assert "long course evidence excerpt" not in client.prompt
    assert "fairness" in client.prompt
