"""EQ7: what happens when something in the pipeline fails?

Section 3.4 requires that a failure must not award progress, and that the
player should still receive a reply. This script injects each failure mode in
turn and records what the system actually does.

Every fault is injected by substituting a deliberately broken LLM client, so
the production code under test is unmodified.

    python -m evaluation.run_degradation
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Iterator

from backend.app.repositories.app_repository import AppRepository
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.evaluator import EvidenceRef
from backend.app.schemas.user import UserCreate
from backend.app.services.conversation_context_service import ConversationContextService
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.level_persuasion_service import LevelPersuasionService
from backend.app.services.llm_client import LLMClientError
from backend.app.services.meter_service import MeterService
from backend.app.services.orchestrator_service import DebateOrchestrator
from backend.app.services.persona_service import PersonaService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.core.config import get_settings

HERE = Path(__file__).parent
RESULTS_DIR = HERE / "results"
INITIAL_METER = 100
ARGUMENT = (
    "Aegis-Recruit was trained on historical hiring data, so data bias will be "
    "carried into its decisions unless you test for it"
)


class TimeoutClient:
    """Provider that always fails, standing in for a timeout or outage."""

    def generate_text(self, *args: Any, **kwargs: Any) -> str:
        raise LLMClientError("simulated provider timeout")

    def stream_text(self, *args: Any, **kwargs: Any) -> Iterator[str]:
        raise LLMClientError("simulated provider timeout")


class InvalidJsonClient:
    """Provider that returns prose where JSON was required."""

    def generate_text(self, *args: Any, **kwargs: Any) -> str:
        return "I think this argument is quite good, maybe eight out of ten."

    def stream_text(self, *args: Any, **kwargs: Any) -> Iterator[str]:
        yield "I think this argument is quite good."


class WrongSchemaClient:
    """Provider that returns valid JSON with the wrong fields."""

    def generate_text(self, *args: Any, **kwargs: Any) -> str:
        return json.dumps({"rating": "excellent", "points": 42})

    def stream_text(self, *args: Any, **kwargs: Any) -> Iterator[str]:
        yield json.dumps({"rating": "excellent"})


class UngroundedStrongClient:
    """Provider claiming a strong verdict with no evidence to support it.

    This is the case the schema rule in Section 4.4 exists to catch.
    """

    def generate_text(self, *args: Any, **kwargs: Any) -> str:
        return json.dumps(
            {
                "match_score": 0.95,
                "score_delta": -28,
                "verdict": "strong",
                "identified_principles": ["fairness"],
                "misconceptions_addressed": [],
                "missing_points": [],
                "evidence_refs": [],
                "reasoning_summary": "Asserted without evidence.",
                "persona_instruction": "Concede.",
                "confidence": 0.99,
            }
        )

    def stream_text(self, *args: Any, **kwargs: Any) -> Iterator[str]:
        yield "{}"


class EmptyRetrievalService:
    """Retrieval that finds nothing, as for an entirely off-topic argument."""

    def retrieve(self, query: Any, top_k: int | None = None) -> list[EvidenceRef]:
        return []


def run_case(
    name: str,
    description: str,
    expectation: str,
    *,
    evaluator_client: Any = None,
    persona_client: Any = None,
    empty_retrieval: bool = False,
) -> dict[str, Any]:
    """Run one fault.

    `expectation` selects the criterion, because the correct outcome differs by
    fault type. An assessment fault must not award progress. A presentation
    fault leaves the verdict intact by design, so a meter change there is
    correct and only the reply matters. The no-provider case is a supported
    mode rather than a fault, and simply has to work end to end.
    """
    settings = get_settings()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        repository = AppRepository(Path(tmp) / "d.db")
        repository.initialize()
        knowledge = KnowledgeRepository(settings.knowledge_db_path)
        retrieval: Any = (
            EmptyRetrievalService()
            if empty_retrieval
            else RetrievalService(knowledge, settings.default_top_k)
        )
        orchestrator = DebateOrchestrator(
            app_repository=repository,
            retrieval_service=retrieval,
            evaluation_service=EvaluationService(llm_client=evaluator_client, max_attempts=2),
            persona_service=PersonaService(llm_client=persona_client, max_attempts=2),
            meter_service=MeterService(),
            conversation_context_service=ConversationContextService(),
            level_persuasion_service=LevelPersuasionService(),
        )
        user = repository.create_user(UserCreate(username="eq7", display_name="EQ7"))
        session = repository.create_session(user.id, 1, INITIAL_METER)

        error: str | None = None
        try:
            response = orchestrator.submit_turn(session.id, ARGUMENT)
            reply = response.npc_response
            outcome = {
                "player_got_reply": bool(reply and reply.strip()),
                "reply_words": len(reply.split()),
                "verdict": response.evaluator.verdict,
                "score_delta": response.score_delta,
                "meter_after": response.meter_after,
                "meter_reduced": response.meter_after < response.meter_before,
                "evaluator_source": response.evaluator_source,
                "persona_source": response.persona_source,
                "turn_persisted": len(repository.fetch_turns(session.id)) == 1,
            }
        except Exception as exc:  # noqa: BLE001 -- recording the failure is the point
            error = f"{type(exc).__name__}: {exc}"
            outcome = {"player_got_reply": False, "meter_reduced": False, "turn_persisted": False}

        baseline = (
            error is None and outcome["player_got_reply"] and outcome["turn_persisted"]
        )
        if expectation == "assessment_must_not_award":
            safe = baseline and not outcome["meter_reduced"]
        else:
            # presentation_fault and supported_mode: the verdict is legitimate,
            # so a meter change is the correct outcome, not a failure.
            safe = baseline

        row = {
            "fault": name,
            "description": description,
            "expectation": expectation,
            "handled_safely": safe,
            "error": error,
            **outcome,
        }
        status = "OK" if safe else "FAIL"
        detail = error or (
            f"verdict={outcome.get('verdict')} delta={outcome.get('score_delta')} "
            f"eval={outcome.get('evaluator_source')} persona={outcome.get('persona_source')}"
        )
        print(f"  [{status}] {name}: {detail}")
        return row


def main() -> None:
    print("EQ7 degradation under injected faults\n")
    rows = [
        run_case(
            "provider_unavailable",
            "No provider configured; services use rule-based paths.",
            "supported_mode",
        ),
        run_case(
            "evaluator_timeout",
            "Evaluator provider raises on every attempt.",
            "assessment_must_not_award",
            evaluator_client=TimeoutClient(),
        ),
        run_case(
            "evaluator_invalid_json",
            "Evaluator provider returns prose instead of JSON.",
            "assessment_must_not_award",
            evaluator_client=InvalidJsonClient(),
        ),
        run_case(
            "evaluator_wrong_schema",
            "Evaluator provider returns JSON with the wrong fields.",
            "assessment_must_not_award",
            evaluator_client=WrongSchemaClient(),
        ),
        run_case(
            "evaluator_ungrounded_strong",
            "Evaluator claims a strong verdict with no evidence attached.",
            "assessment_must_not_award",
            evaluator_client=UngroundedStrongClient(),
        ),
        run_case(
            "empty_retrieval",
            "Retrieval returns no evidence at all.",
            "assessment_must_not_award",
            empty_retrieval=True,
        ),
        run_case(
            "persona_timeout",
            "Persona provider fails; evaluation is unaffected.",
            "presentation_fault",
            persona_client=TimeoutClient(),
        ),
        run_case(
            "persona_invalid_json",
            "Persona provider returns unusable output.",
            "presentation_fault",
            persona_client=InvalidJsonClient(),
        ),
    ]

    safe = sum(1 for r in rows if r["handled_safely"])
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "eq7_degradation.json").write_text(
        json.dumps({"safe": safe, "total": len(rows), "faults": rows}, indent=2),
        encoding="utf-8",
    )
    print(f"\n{safe}/{len(rows)} faults met their expected criterion")
    print(f"Written to {RESULTS_DIR / 'eq7_degradation.json'}")


if __name__ == "__main__":
    main()
