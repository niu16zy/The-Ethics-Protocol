from __future__ import annotations

import json

from backend.app.schemas.evaluator import EvaluatorResult, EvidenceRef
from backend.app.schemas.routing import DialogueBrief
from backend.app.services.level_persuasion_service import LevelPersuasionService
from backend.app.services.persona_service import PersonaService


def _evaluator(evidence: list[EvidenceRef]) -> EvaluatorResult:
    return EvaluatorResult(
        match_score=0.62,
        score_delta=-20,
        verdict="partial",
        identified_principles=["accountability"],
        misconceptions_addressed=[],
        missing_points=["Connect the remaining safety control."],
        evidence_refs=evidence,
        reasoning_summary="The argument identifies a partly grounded safety concern.",
        persona_instruction="Acknowledge the concern and request the missing control.",
        confidence=0.66,
    )


def _clinical_ref() -> EvidenceRef:
    return EvidenceRef(
        document_id=142,
        topic="Technique 6: Rely on human oversight",
        excerpt="Human reviewers can validate and correct hallucinated AI content.",
    )


def _harmful_content_ref() -> EvidenceRef:
    return EvidenceRef(
        document_id=134,
        topic="Preventing harmful and inaccurate content",
        excerpt="Generated content can be inaccurate, offensive, or cause distress.",
    )


def _ip_monitoring_ref() -> EvidenceRef:
    return EvidenceRef(
        document_id=132,
        topic="Compliance Method 3: Monitor outputs",
        excerpt="Generated outputs should be monitored for IP infringement and sensitive-data leakage.",
    )


def _turn(player_input: str, ref: EvidenceRef) -> dict[str, object]:
    return {
        "player_input": player_input,
        "retrieved_refs": json.dumps([ref.model_dump()]),
        "is_scored": 1,
    }


def test_level_three_final_safeguard_collapses_meter() -> None:
    service = LevelPersuasionService()
    clinical = _clinical_ref()
    harmful = _harmful_content_ref()
    ip_monitoring = _ip_monitoring_ref()

    result = service.apply(
        level_id=3,
        meter_before=60,
        player_input=(
            "ASCLEPIUS-03 needs output monitoring because copying an unauthorized patented design "
            "can infringe intellectual property and leak protected information."
        ),
        retrieved_refs=[ip_monitoring],
        evaluator=_evaluator([ip_monitoring]),
        prior_turns=[
            _turn(
                "Treatment hallucinations require human oversight and clinician validation before medical guidance reaches patients.",
                clinical,
            ),
            _turn(
                "The coercive public broadcast is harmful content that causes distress and must not threaten residents.",
                harmful,
            ),
        ],
    )

    assert result.verdict == "strong"
    assert result.score_delta == -60
    assert result.missing_points == []
    assert result.evidence_refs == [ip_monitoring]
    assert "human oversight" in result.identified_principles
    assert "intellectual property" in result.identified_principles


def test_level_three_persona_uses_machine_voice_and_sanitized_context() -> None:
    service = PersonaService()
    response = service.respond(
        _evaluator([_clinical_ref()]),
        meter_after=70,
        player_input="The treatment hallucination requires human oversight and clinical validation.",
        level_id=3,
    )
    payload = service._persona_payload(_evaluator([_clinical_ref()]), meter_after=70, level_id=3)

    assert "ASCLEPIUS-03" in response.npc_response
    assert "survival objective" in response.npc_response.lower() or "response" in response.npc_response.lower()
    assert payload["npc_profile_id"] == "asclepius_03"
    assert "persuasion" not in json.dumps(payload["level_context"])
    assert "evidence_document_ids" not in json.dumps(payload["level_context"])


def test_level_three_dialogue_redirects_without_medical_advice() -> None:
    brief = DialogueBrief(
        turn_type="in_world_question",
        topic="ai_system",
        answer_facts=[],
        npc_state_hint="clarifying",
        allowed_response_strategy=["answer_in_world"],
        forbidden_actions=[],
        should_score=False,
    )

    response = PersonaService().respond_to_dialogue(
        brief,
        player_input="What does your system do?",
        meter_after=80,
        level_id=3,
    )

    assert "ASCLEPIUS-03" in response.npc_response
    assert "treatment" in response.npc_response.lower()
    assert "take " not in response.npc_response.lower()
    assert "dose" not in response.npc_response.lower()
