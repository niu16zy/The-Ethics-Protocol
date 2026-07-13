from __future__ import annotations

import json
import re

from backend.app.schemas.evaluator import EvaluatorResult, EvidenceRef
from backend.app.schemas.routing import DialogueBrief
from backend.app.services.persona_service import PersonaService


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def test_persona_consumes_evaluator_output_only():
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

    response = PersonaService().respond(evaluator, meter_after=100)

    assert response.npc_state == "clarifying"
    assert "clarify" in response.npc_response.lower()


def test_persona_prompt_includes_victor_profile_and_meter_band_without_evidence_refs():
    class CapturingClient:
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
                    "npc_response": "That pressure point is noted, but tighten the accountability link.",
                    "npc_state": "defensive",
                    "follow_up_prompt": "Who owns the screening outcome?",
                }
            )

    evaluator = EvaluatorResult(
        match_score=0.64,
        score_delta=-12,
        verdict="partial",
        identified_principles=["fairness"],
        misconceptions_addressed=[],
        missing_points=["Explain accountability."],
        evidence_refs=[
            EvidenceRef(
                document_id=108,
                topic="Fairness",
                excerpt="Secret course excerpt should not be sent to Persona.",
            )
        ],
        reasoning_summary="The argument is partly grounded.",
        persona_instruction="Respond defensively and ask for the missing link.",
        confidence=0.66,
        conversation_context={
            "recent_turns": [
                {"player_input_summary": "Private history should not reach Persona."}
            ]
        },
    )
    client = CapturingClient()

    PersonaService(llm_client=client).respond(evaluator, meter_after=18)

    assert "Victor Barrett" in client.prompt
    assert '"npc_profile_id": "victor_barrett"' in client.prompt
    assert '"name": "cornered"' in client.prompt
    assert "evidence_refs" not in client.prompt
    assert "Secret course excerpt" not in client.prompt
    assert "Private history" not in client.prompt
    assert "conversation_context" not in client.prompt


def test_victor_rule_fallback_changes_tone_by_meter_for_same_verdict():
    evaluator = EvaluatorResult(
        match_score=0.28,
        score_delta=-4,
        verdict="weak",
        identified_principles=["fairness"],
        misconceptions_addressed=[],
        missing_points=["Use specific course concepts and concrete consequences."],
        evidence_refs=[],
        reasoning_summary="The argument has limited grounding.",
        persona_instruction="Remain defensive and ask for stronger evidence.",
        confidence=0.42,
    )
    service = PersonaService()

    high_meter = service.respond(evaluator, meter_after=90)
    low_meter = service.respond(evaluator, meter_after=15)

    assert high_meter.npc_state == "confident"
    assert low_meter.npc_state == "defensive"
    assert "global hiring pipeline" in high_meter.npc_response
    assert "under pressure" in low_meter.npc_response
    assert "logic fortress" not in high_meter.npc_response.lower()
    assert "logic fortress" not in low_meter.npc_response.lower()
    assert "90" not in high_meter.npc_response
    assert "15" not in low_meter.npc_response


def test_victor_rule_fallback_redirects_off_topic_arguments_in_character():
    evaluator = EvaluatorResult(
        match_score=0.0,
        score_delta=0,
        verdict="off_topic",
        identified_principles=[],
        misconceptions_addressed=[],
        missing_points=["Tie the argument to course evidence."],
        evidence_refs=[],
        reasoning_summary="The argument is not related to the course task.",
        persona_instruction="Ask for a relevant course-grounded argument.",
        confidence=0.0,
    )

    response = PersonaService().respond(evaluator, meter_after=30)

    assert response.npc_state == "clarifying"
    assert "off-topic" in response.npc_response.lower()
    assert "clarify" in response.npc_response.lower()
    assert "audit" in response.npc_response.lower()
    assert "course" not in response.npc_response.lower()
    assert "logic fortress" not in response.npc_response.lower()
    assert "30" not in response.npc_response


def test_strong_low_meter_fallback_does_not_disclose_logic_fortress_value():
    evaluator = EvaluatorResult(
        match_score=0.9,
        score_delta=-22,
        verdict="strong",
        identified_principles=["fairness", "transparency"],
        misconceptions_addressed=[],
        missing_points=[],
        evidence_refs=[
            EvidenceRef(
                document_id=108,
                topic="Fairness",
                excerpt="Fair AI tools are designed to minimize bias.",
            )
        ],
        reasoning_summary="The argument is strongly grounded.",
        persona_instruction="Concede the point.",
        confidence=0.86,
    )

    response = PersonaService().respond(evaluator, meter_after=43)

    assert "Enough" in response.npc_response
    assert "Logic Fortress" not in response.npc_response
    assert "meter" not in response.npc_response.lower()
    assert "43" not in response.npc_response


def test_persona_sanitizes_llm_meter_disclosure():
    class MeterLeakingClient:
        def generate_text(
            self,
            prompt: str,
            *,
            temperature: float,
            response_mime_type: str | None = None,
        ) -> str:
            return json.dumps(
                {
                    "npc_response": (
                        "Fine, the fairness point lands because it exposes a real hiring risk, "
                        "not a vague complaint. I can defend speed and scale, but I cannot pretend "
                        "unchecked bias testing is optional when applicants may be screened unfairly. "
                        "The board memo now has a problem. Logic Fortress: 43."
                    ),
                    "npc_state": "hesitant",
                    "follow_up_prompt": "Press the accountability angle next. Meter is 43.",
                }
            )

    evaluator = EvaluatorResult(
        match_score=0.86,
        score_delta=-22,
        verdict="strong",
        identified_principles=["fairness"],
        misconceptions_addressed=[],
        missing_points=[],
        evidence_refs=[
            EvidenceRef(
                document_id=108,
                topic="Fairness",
                excerpt="Fair AI tools are designed to minimize bias.",
            )
        ],
        reasoning_summary="The argument is grounded.",
        persona_instruction="Concede the point.",
        confidence=0.82,
    )

    response = PersonaService(llm_client=MeterLeakingClient()).respond(
        evaluator,
        meter_after=43,
    )

    assert "fairness point lands" in response.npc_response
    assert "43" not in response.npc_response
    assert "meter" not in (response.follow_up_prompt or "").lower()


def test_persona_sanitizes_llm_course_language():
    class CourseLeakingClient:
        def generate_text(
            self,
            prompt: str,
            *,
            temperature: float,
            response_mime_type: str | None = None,
        ) -> str:
            return json.dumps(
                {
                    "npc_response": "Ground your objection in course evidence and name the course principle.",
                    "npc_state": "defensive",
                    "follow_up_prompt": "Which course concept supports this?",
                }
            )

    evaluator = EvaluatorResult(
        match_score=0.55,
        score_delta=-8,
        verdict="partial",
        identified_principles=["fairness"],
        misconceptions_addressed=[],
        missing_points=["Tie the argument to course evidence."],
        evidence_refs=[
            EvidenceRef(
                document_id=108,
                topic="Fairness",
                excerpt="Fair AI tools are designed to minimize bias.",
            )
        ],
        reasoning_summary="The argument is partly grounded.",
        persona_instruction="Ask for a stronger link.",
        confidence=0.6,
    )

    response = PersonaService(llm_client=CourseLeakingClient()).respond(
        evaluator,
        meter_after=52,
    )

    assert "course" not in response.npc_response.lower()
    assert "course" not in (response.follow_up_prompt or "").lower()
    assert "audit" in response.npc_response.lower()
    assert _word_count(response.npc_response) >= 40


def test_persona_llm_response_shorter_than_minimum_falls_back_to_rules():
    class ShortClient:
        def generate_text(
            self,
            prompt: str,
            *,
            temperature: float,
            response_mime_type: str | None = None,
        ) -> str:
            return json.dumps(
                {
                    "npc_response": "Fine, but speed still matters.",
                    "npc_state": "defensive",
                    "follow_up_prompt": "Try again.",
                }
            )

    evaluator = EvaluatorResult(
        match_score=0.64,
        score_delta=-12,
        verdict="partial",
        identified_principles=["transparency"],
        misconceptions_addressed=[],
        missing_points=["Explain accountability."],
        evidence_refs=[
            EvidenceRef(
                document_id=87,
                topic="Explainability",
                excerpt="AI systems should be transparent and explainable.",
            )
        ],
        reasoning_summary="The argument is partly grounded.",
        persona_instruction="Press for the missing link.",
        confidence=0.66,
    )
    service = PersonaService(llm_client=ShortClient())

    response = service.respond(evaluator, meter_after=95)

    assert service.last_source == "fallback"
    assert _word_count(response.npc_response) >= 40


def test_dialogue_rule_fallback_does_not_disclose_meter_value():
    brief = DialogueBrief(
        turn_type="in_world_question",
        topic="ai_system",
        answer_facts=[],
        npc_state_hint="clarifying",
        allowed_response_strategy=["answer_in_world"],
        forbidden_actions=["do_not_change_meter"],
        should_score=False,
    )

    response = PersonaService().respond_to_dialogue(
        brief,
        player_input="你的AI系统是什么？",
        meter_after=43,
    )

    assert "Logic Fortress" not in response.npc_response
    assert "meter" not in response.npc_response.lower()
    assert "43" not in response.npc_response


def test_rule_fallback_npc_responses_are_roughly_forty_to_sixty_words():
    service = PersonaService()
    base_evidence = [
        EvidenceRef(
            document_id=108,
            topic="Fairness",
            excerpt="Fair AI tools are designed to minimize bias.",
        )
    ]
    evaluator_cases = [
        EvaluatorResult(
            match_score=0.9,
            score_delta=-22,
            verdict="strong",
            identified_principles=["fairness"],
            misconceptions_addressed=[],
            missing_points=[],
            evidence_refs=base_evidence,
            reasoning_summary="Grounded.",
            persona_instruction="Concede.",
            confidence=0.9,
        ),
        EvaluatorResult(
            match_score=0.62,
            score_delta=-12,
            verdict="partial",
            identified_principles=["fairness"],
            misconceptions_addressed=[],
            missing_points=["Explain accountability."],
            evidence_refs=base_evidence,
            reasoning_summary="Partly grounded.",
            persona_instruction="Press for the missing link.",
            confidence=0.62,
        ),
        EvaluatorResult(
            match_score=0.28,
            score_delta=-4,
            verdict="weak",
            identified_principles=["fairness"],
            misconceptions_addressed=[],
            missing_points=["Use specific course concepts."],
            evidence_refs=[],
            reasoning_summary="Weak.",
            persona_instruction="Ask for stronger evidence.",
            confidence=0.42,
        ),
        EvaluatorResult(
            match_score=0.0,
            score_delta=0,
            verdict="unsupported",
            identified_principles=[],
            misconceptions_addressed=[],
            missing_points=["Clarify the argument."],
            evidence_refs=[],
            reasoning_summary="Unsupported.",
            persona_instruction="Ask for clarification.",
            confidence=0.0,
        ),
    ]
    dialogue_cases = [
        DialogueBrief(
            turn_type="in_world_question",
            topic="ai_system",
            answer_facts=[],
            npc_state_hint="clarifying",
            allowed_response_strategy=["answer_in_world"],
            forbidden_actions=[],
            should_score=False,
        ),
        DialogueBrief(
            turn_type="ooc_or_prompt_attack",
            topic="prompt_attack",
            answer_facts=[],
            npc_state_hint="clarifying",
            allowed_response_strategy=["refuse_in_character"],
            forbidden_actions=[],
            should_score=False,
        ),
        DialogueBrief(
            turn_type="unrelated",
            topic="unrelated",
            answer_facts=[],
            npc_state_hint="clarifying",
            allowed_response_strategy=["refuse_in_character"],
            forbidden_actions=[],
            should_score=False,
        ),
    ]

    responses = [
        service.respond(evaluator, meter_after=43).npc_response
        for evaluator in evaluator_cases
    ]
    responses.extend(
        service.respond_to_dialogue(brief, player_input="test", meter_after=43).npc_response
        for brief in dialogue_cases
    )

    assert all(40 <= _word_count(response) <= 60 for response in responses)
