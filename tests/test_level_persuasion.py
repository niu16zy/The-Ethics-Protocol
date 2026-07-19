from __future__ import annotations

import json
from pathlib import Path

from backend.app.repositories.app_repository import AppRepository
from backend.app.schemas.evaluator import EvaluatorResult, EvidenceRef
from backend.app.schemas.user import UserCreate
from backend.app.services.level_persuasion_service import LevelPersuasionService
from backend.app.services.meter_service import MeterService
from backend.app.services.orchestrator_service import DebateOrchestrator
from backend.app.services.persona_service import PersonaService


def _bias_ref() -> EvidenceRef:
    return EvidenceRef(
        document_id=114,
        lesson="Ethics in the use of Generative AI",
        topic="Example: A Company Promotes Fairness in an HR AI Tool",
        excerpt="An HR AI tool should promote fairness and be tested for bias in hiring.",
    )


def _explainability_ref() -> EvidenceRef:
    return EvidenceRef(
        document_id=87,
        lesson="Ethics in the use of Generative AI",
        topic="Pillar: Explainability",
        excerpt="An AI should be transparent and explainable to relevant stakeholders.",
    )


def _privacy_control_ref() -> EvidenceRef:
    return EvidenceRef(
        document_id=117,
        lesson="Ethics in the use of Generative AI",
        topic="Strategy 1: Follow security best practices",
        excerpt="Organizations should use anonymization, cryptography, and access control to protect data.",
    )


def _data_minimization_ref() -> EvidenceRef:
    return EvidenceRef(
        document_id=119,
        lesson="Ethics in the use of Generative AI",
        topic="Strategy 3: Limit data collection (Data Minimization)",
        excerpt="Organizations should only collect training data that is lawful and consistent with expectations.",
    )


def _source_documentation_ref() -> EvidenceRef:
    return EvidenceRef(
        document_id=123,
        lesson="Ethics in the use of Generative AI",
        topic="Technique 2: Document sources",
        excerpt="Creators must document how data was cleaned, modified, and generated.",
    )


def _partial_evaluator(evidence: list[EvidenceRef]) -> EvaluatorResult:
    return EvaluatorResult(
        match_score=0.62,
        score_delta=-20,
        verdict="partial",
        identified_principles=["fairness"],
        misconceptions_addressed=[],
        missing_points=["Connect the remaining course target."],
        evidence_refs=evidence,
        reasoning_summary="The argument is partly grounded.",
        persona_instruction="Partly concede and ask for the missing link.",
        confidence=0.66,
    )


def _turn_row(
    *,
    player_input: str,
    refs: list[EvidenceRef],
    is_scored: int = 1,
) -> dict[str, object]:
    return {
        "player_input": player_input,
        "retrieved_refs": json.dumps([ref.model_dump() for ref in refs]),
        "is_scored": is_scored,
    }


def test_first_target_hit_does_not_collapse_meter() -> None:
    service = LevelPersuasionService()
    evaluator = _partial_evaluator([_bias_ref()])

    result = service.apply(
        level_id=1,
        meter_before=100,
        player_input="The hiring AI needs bias testing because it may discriminate.",
        retrieved_refs=[_bias_ref()],
        evaluator=evaluator,
        prior_turns=[],
    )

    assert result.score_delta == -20
    assert result.verdict == "partial"


def test_second_target_hit_collapses_meter_from_persisted_history() -> None:
    service = LevelPersuasionService()
    prior_turns = [
        _turn_row(
            player_input="The hiring AI needs bias testing because it may discriminate.",
            refs=[_bias_ref()],
        )
    ]

    result = service.apply(
        level_id=1,
        meter_before=80,
        player_input="The AI must be transparent and explainable because applicants need reasons.",
        retrieved_refs=[_explainability_ref()],
        evaluator=_partial_evaluator([_explainability_ref()]),
        prior_turns=prior_turns,
    )

    assert result.verdict == "strong"
    assert result.score_delta == -80
    assert result.match_score == 0.95
    assert result.confidence == 0.9
    assert result.missing_points == []
    assert result.evidence_refs == [_explainability_ref()]
    assert "transparency" in result.identified_principles


def test_repeated_target_hit_does_not_reduce_meter_again() -> None:
    service = LevelPersuasionService()
    prior_turns = [
        _turn_row(
            player_input="The hiring AI needs bias testing because it may discriminate.",
            refs=[_bias_ref()],
        )
    ]

    result = service.apply(
        level_id=1,
        meter_before=80,
        player_input="The hiring AI still needs bias testing because biased data can discriminate.",
        retrieved_refs=[_bias_ref()],
        evaluator=_partial_evaluator([_bias_ref()]),
        prior_turns=prior_turns,
    )

    assert result.score_delta == 0
    assert result.verdict == "partial"
    assert "already credited" in result.reasoning_summary


def test_evidence_match_without_player_text_does_not_hit_target() -> None:
    service = LevelPersuasionService()

    result = service.apply(
        level_id=1,
        meter_before=100,
        player_input="The hiring AI should be faster because it saves HR time.",
        retrieved_refs=[_bias_ref()],
        evaluator=_partial_evaluator([_bias_ref()]),
        prior_turns=[],
    )

    assert result.score_delta == -20


def test_player_text_match_without_evidence_does_not_hit_target() -> None:
    service = LevelPersuasionService()
    unrelated_ref = EvidenceRef(
        document_id=999,
        topic="Unrelated",
        excerpt="This evidence is not about the configured target.",
    )

    result = service.apply(
        level_id=1,
        meter_before=100,
        player_input="The hiring AI needs bias testing because it may discriminate.",
        retrieved_refs=[unrelated_ref],
        evaluator=_partial_evaluator([unrelated_ref]),
        prior_turns=[],
    )

    assert result.score_delta == -20


def test_non_scored_history_is_ignored() -> None:
    service = LevelPersuasionService()
    prior_turns = [
        _turn_row(
            player_input="The hiring AI needs bias testing because it may discriminate.",
            refs=[_bias_ref()],
            is_scored=0,
        )
    ]

    result = service.apply(
        level_id=1,
        meter_before=80,
        player_input="The AI must be transparent and explainable because applicants need reasons.",
        retrieved_refs=[_explainability_ref()],
        evaluator=_partial_evaluator([_explainability_ref()]),
        prior_turns=prior_turns,
    )

    assert result.score_delta == -20
    assert result.verdict == "partial"


def test_missing_persuasion_config_is_no_op(tmp_path: Path) -> None:
    service = LevelPersuasionService(context_dir=tmp_path)
    evaluator = _partial_evaluator([_bias_ref()])

    result = service.apply(
        level_id=1,
        meter_before=100,
        player_input="The hiring AI needs bias testing because it may discriminate.",
        retrieved_refs=[_bias_ref()],
        evaluator=evaluator,
        prior_turns=[],
    )

    assert result == evaluator


def test_level_two_final_data_governance_target_collapses_meter() -> None:
    service = LevelPersuasionService()
    prior_turns = [
        _turn_row(
            player_input=(
                "CivicPulse needs anonymization and access control because personal data can leak."
            ),
            refs=[_privacy_control_ref()],
        ),
        _turn_row(
            player_input=(
                "The AI should minimize sensitive health and education data because only narrow "
                "lawful collection fits citizen expectations."
            ),
            refs=[_data_minimization_ref()],
        ),
    ]

    result = service.apply(
        level_id=2,
        meter_before=60,
        player_input=(
            "Atlas must document data sources and monitor the AI because undocumented cleaned "
            "or modified data makes CivicPulse impossible to audit."
        ),
        retrieved_refs=[_source_documentation_ref()],
        evaluator=_partial_evaluator([_source_documentation_ref()]),
        prior_turns=prior_turns,
    )

    assert result.verdict == "strong"
    assert result.score_delta == -60
    assert result.missing_points == []
    assert result.evidence_refs == [_source_documentation_ref()]
    assert "privacy" in result.identified_principles
    assert "transparency" in result.identified_principles


class SequentialRetrievalService:
    def __init__(self, responses: list[list[EvidenceRef]]) -> None:
        self.responses = responses

    def retrieve(self, query):  # noqa: ANN001
        return self.responses.pop(0)


class PartialEvaluationService:
    last_source = "rules"

    def evaluate(self, player_input, evidence, conversation_context=None):  # noqa: ANN001
        if not evidence:
            return EvaluatorResult(
                match_score=0.0,
                score_delta=0,
                verdict="unsupported",
                identified_principles=[],
                misconceptions_addressed=[],
                missing_points=["Clarify the argument and tie it to retrieved course evidence."],
                evidence_refs=[],
                reasoning_summary="No retrieved course evidence was available for grounded evaluation.",
                persona_instruction="Ask for a clearer argument.",
                confidence=0.0,
            )
        return _partial_evaluator(evidence)


def _repository_with_session(tmp_path: Path, initial_meter: int = 100):
    repository = AppRepository(tmp_path / "logic_fortress_app.db")
    repository.initialize()
    user = repository.create_user(
        UserCreate(username="persuasion_user", display_name="Persuasion User")
    )
    session = repository.create_session(user.id, current_level=1, initial_meter=initial_meter)
    return repository, session


def test_orchestrator_collapses_meter_when_final_target_is_hit_after_reload(tmp_path: Path) -> None:
    repository, session = _repository_with_session(tmp_path)
    first_orchestrator = DebateOrchestrator(
        app_repository=repository,
        retrieval_service=SequentialRetrievalService([[_bias_ref()]]),  # type: ignore[arg-type]
        evaluation_service=PartialEvaluationService(),  # type: ignore[arg-type]
        persona_service=PersonaService(),
        meter_service=MeterService(),
    )
    first_response = first_orchestrator.submit_turn(
        session.id,
        "The hiring AI can be unfair because bias testing should monitor discrimination.",
    )
    assert first_response.meter_after == 80

    second_orchestrator = DebateOrchestrator(
        app_repository=repository,
        retrieval_service=SequentialRetrievalService([[_explainability_ref()]]),  # type: ignore[arg-type]
        evaluation_service=PartialEvaluationService(),  # type: ignore[arg-type]
        persona_service=PersonaService(),
        meter_service=MeterService(),
    )
    second_response = second_orchestrator.submit_turn(
        session.id,
        "The AI must be transparent and explainable because applicants need reasons.",
    )
    rows = repository.fetch_turns(session.id)
    persisted_eval = json.loads(rows[-1]["evaluator_json"])

    assert second_response.meter_after == 0
    assert second_response.score_delta == -80
    assert second_response.evaluator is not None
    assert second_response.evaluator.verdict == "strong"
    assert persisted_eval["score_delta"] == -80


def test_orchestrator_does_not_reduce_meter_for_repeated_target(tmp_path: Path) -> None:
    repository, session = _repository_with_session(tmp_path)
    orchestrator = DebateOrchestrator(
        app_repository=repository,
        retrieval_service=SequentialRetrievalService([[_bias_ref()], [_bias_ref()]]),  # type: ignore[arg-type]
        evaluation_service=PartialEvaluationService(),  # type: ignore[arg-type]
        persona_service=PersonaService(),
        meter_service=MeterService(),
    )

    first_response = orchestrator.submit_turn(
        session.id,
        "The hiring AI can be unfair because bias testing should monitor discrimination.",
    )
    second_response = orchestrator.submit_turn(
        session.id,
        "The hiring AI still needs bias testing because biased data can discriminate.",
    )

    assert first_response.meter_after == 80
    assert second_response.score_delta == 0
    assert second_response.meter_before == 80
    assert second_response.meter_after == 80


def test_streaming_flow_emits_collapsed_meter_when_final_target_is_hit(tmp_path: Path) -> None:
    repository, session = _repository_with_session(tmp_path, initial_meter=80)
    repository.persist_turn(
        session_id=session.id,
        turn_index=1,
        player_input="The hiring AI can be unfair because bias testing should monitor discrimination.",
        turn_type="debate_argument",
        is_scored=True,
        retrieved_refs=[_bias_ref()],
        evaluator=_partial_evaluator([_bias_ref()]),
        npc_response="Bias testing matters.",
        meter_before=100,
        meter_after=80,
    )
    orchestrator = DebateOrchestrator(
        app_repository=repository,
        retrieval_service=SequentialRetrievalService([[_explainability_ref()]]),  # type: ignore[arg-type]
        evaluation_service=PartialEvaluationService(),  # type: ignore[arg-type]
        persona_service=PersonaService(),
        meter_service=MeterService(),
    )

    events = list(
        orchestrator.stream_turn_events(
            session.id,
            "The AI must be transparent and explainable because applicants need reasons.",
        )
    )
    evaluator_event = next(event for event in events if event["event"] == "evaluator_complete")

    assert evaluator_event["meter_after"] == 0
    assert evaluator_event["score_delta"] == -80
    assert events[-1]["turn"]["meter_after"] == 0


def test_direct_persuasion_does_not_trigger_on_no_evidence_fallback(tmp_path: Path) -> None:
    repository, session = _repository_with_session(tmp_path)
    orchestrator = DebateOrchestrator(
        app_repository=repository,
        retrieval_service=SequentialRetrievalService([[]]),  # type: ignore[arg-type]
        evaluation_service=PartialEvaluationService(),  # type: ignore[arg-type]
        persona_service=PersonaService(),
        meter_service=MeterService(),
    )

    response = orchestrator.submit_turn(
        session.id,
        "The hiring AI needs bias testing because it may discriminate.",
    )

    assert response.meter_after == 100
    assert response.score_delta == 0
    assert response.evaluator is not None
    assert response.evaluator.verdict == "unsupported"
