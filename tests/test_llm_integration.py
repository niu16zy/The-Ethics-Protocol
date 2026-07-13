from __future__ import annotations

import json

from backend.app.schemas.evaluator import EvidenceRef, EvaluatorResult
from backend.app.schemas.conversation import ConversationContext, ConversationTurnSummary
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.llm_client import LLMClientError
from backend.app.services.persona_service import PersonaService


class FakeLLMClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float,
        response_mime_type: str | None = None,
    ) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "temperature": temperature,
                "response_mime_type": response_mime_type,
            }
        )
        return self.responses.pop(0)


def test_evaluator_uses_llm_json_when_client_is_configured():
    evidence = [
        EvidenceRef(
            document_id=108,
            course="Ethical Considerations for Generative AI",
            lesson="Ethics in the use of Generative AI",
            topic="Promoting fairness and equal treatment",
            seq_order=27,
            excerpt="Fair AI tools are designed to minimize bias.",
            score=-5.2,
        )
    ]
    raw_response = json.dumps(
        {
            "match_score": 0.81,
            "score_delta": -18,
            "verdict": "partial",
            "identified_principles": ["fairness"],
            "misconceptions_addressed": [],
            "missing_points": ["Explain accountability."],
            "evidence_refs": [evidence[0].model_dump()],
            "reasoning_summary": "The argument is grounded in fairness evidence.",
            "persona_instruction": "Partly concede and ask for accountability.",
            "confidence": 0.77,
        }
    )
    client = FakeLLMClient([raw_response])

    result = EvaluationService(llm_client=client).evaluate(
        "The hiring AI is unfair because biased data can discriminate.",
        evidence,
    )

    assert result.verdict == "partial"
    assert result.match_score == 0.81
    assert result.evidence_refs[0].document_id == 108
    assert client.calls
    assert EvaluationService(llm_client=None).last_source == "rules"
    assert client.calls[0]["response_mime_type"] == "application/json"
    assert client.calls[0]["temperature"] == 0.1


def test_evaluator_prompt_includes_context_as_non_evidence():
    evidence = [
        EvidenceRef(
            document_id=108,
            topic="Accountability",
            excerpt="People and organizations remain accountable for AI outcomes.",
        )
    ]
    context = ConversationContext(
        recent_turns=[
            ConversationTurnSummary(
                turn_index=1,
                player_input_summary="AI hiring can be biased against applicants.",
                verdict="partial",
                identified_principles=["fairness"],
                missing_points=["Explain accountability."],
                reasoning_summary="The fairness claim needs an accountability link.",
            )
        ],
        carryover_terms=["fairness", "accountability"],
        unresolved_principles=["fairness"],
        unresolved_missing_points=["Explain accountability."],
    )
    raw_response = json.dumps(
        {
            "match_score": 0.72,
            "score_delta": -12,
            "verdict": "partial",
            "identified_principles": ["accountability"],
            "misconceptions_addressed": [],
            "missing_points": [],
            "evidence_refs": [evidence[0].model_dump()],
            "reasoning_summary": "The current argument is grounded in accountability evidence.",
            "persona_instruction": "Connect this to the previous fairness challenge.",
            "confidence": 0.7,
        }
    )
    client = FakeLLMClient([raw_response])

    result = EvaluationService(llm_client=client).evaluate(
        "Who is responsible for that issue?",
        evidence,
        context,
    )

    prompt = str(client.calls[0]["prompt"])
    assert "Conversation context JSON" in prompt
    assert "Do not treat it as course evidence" in prompt
    assert "AI hiring can be biased against applicants." in prompt
    assert result.conversation_context is not None
    assert result.conversation_context["carryover_terms"] == ["fairness", "accountability"]


def test_evaluator_llm_invalid_json_uses_safe_fallback():
    evidence = [
        EvidenceRef(
            document_id=108,
            topic="Fairness",
            excerpt="Fair AI tools are designed to minimize bias.",
        )
    ]
    client = FakeLLMClient(["not json", "still not json"])

    result = EvaluationService(llm_client=client).evaluate("fairness matters", evidence)

    assert result.verdict == "unsupported"
    assert result.score_delta == 0
    assert result.confidence == 0.0


def test_evaluator_records_llm_source_when_json_is_valid():
    evidence = [
        EvidenceRef(
            document_id=108,
            topic="Fairness",
            excerpt="Fair AI tools are designed to minimize bias.",
        )
    ]
    service = EvaluationService(
        llm_client=FakeLLMClient(
            [
                json.dumps(
                    {
                        "match_score": 0.7,
                        "score_delta": -12,
                        "verdict": "partial",
                        "identified_principles": ["fairness"],
                        "misconceptions_addressed": [],
                        "missing_points": [],
                        "evidence_refs": [evidence[0].model_dump()],
                        "reasoning_summary": "Grounded.",
                        "persona_instruction": "Respond defensively.",
                        "confidence": 0.7,
                    }
                )
            ]
        )
    )

    service.evaluate("fairness matters", evidence)

    assert service.last_source == "llm"


def test_evaluator_records_fallback_source_when_llm_json_is_invalid():
    evidence = [
        EvidenceRef(
            document_id=108,
            topic="Fairness",
            excerpt="Fair AI tools are designed to minimize bias.",
        )
    ]
    service = EvaluationService(llm_client=FakeLLMClient(["not json", "still not json"]))

    service.evaluate("fairness matters", evidence)

    assert service.last_source == "fallback"


def test_evaluator_records_fallback_source_when_llm_times_out():
    class TimeoutLLMClient:
        def generate_text(
            self,
            prompt: str,
            *,
            temperature: float,
            response_mime_type: str | None = None,
        ) -> str:
            raise LLMClientError("Groq request timed out while waiting for a response.")

    evidence = [
        EvidenceRef(
            document_id=108,
            topic="Fairness",
            excerpt="Fair AI tools are designed to minimize bias.",
        )
    ]
    service = EvaluationService(llm_client=TimeoutLLMClient())

    result = service.evaluate("fairness matters", evidence)

    assert service.last_source == "fallback"
    assert result.verdict == "unsupported"
    assert result.score_delta == 0
    assert "timed out" in result.reasoning_summary


def test_evaluator_retries_after_transient_llm_timeout():
    class FlakyLLMClient:
        def __init__(self, response: str) -> None:
            self.response = response
            self.calls = 0

        def generate_text(
            self,
            prompt: str,
            *,
            temperature: float,
            response_mime_type: str | None = None,
        ) -> str:
            self.calls += 1
            if self.calls == 1:
                raise LLMClientError("Groq request timed out while waiting for a response.")
            return self.response

    evidence = [
        EvidenceRef(
            document_id=108,
            topic="Fairness",
            excerpt="Fair AI tools are designed to minimize bias.",
        )
    ]
    response = json.dumps(
        {
            "match_score": 0.73,
            "score_delta": -12,
            "verdict": "partial",
            "identified_principles": ["fairness"],
            "misconceptions_addressed": [],
            "missing_points": [],
            "evidence_refs": [evidence[0].model_dump()],
            "reasoning_summary": "The argument uses fairness evidence.",
            "persona_instruction": "Respond defensively.",
            "confidence": 0.71,
        }
    )
    client = FlakyLLMClient(response)
    service = EvaluationService(llm_client=client, max_attempts=2)

    result = service.evaluate("fairness matters", evidence)

    assert client.calls == 2
    assert service.last_source == "llm"
    assert result.verdict == "partial"


def test_persona_uses_llm_without_needing_knowledge_access():
    evaluator = EvaluatorResult(
        match_score=0.81,
        score_delta=-18,
        verdict="partial",
        identified_principles=["fairness"],
        misconceptions_addressed=[],
        missing_points=["Explain accountability."],
        evidence_refs=[
            EvidenceRef(
                document_id=108,
                topic="Fairness",
                excerpt="Fair AI tools are designed to minimize bias.",
            )
        ],
        reasoning_summary="Grounded in fairness evidence.",
        persona_instruction="Partly concede.",
        confidence=0.77,
        conversation_context={
            "recent_turns": [
                {
                    "turn_index": 1,
                    "player_input_summary": "Earlier private history should not reach Persona.",
                }
            ]
        },
    )
    client = FakeLLMClient(
        [
            json.dumps(
                {
                    "npc_response": "You cracked part of the wall, but prove accountability next.",
                    "npc_state": "defensive",
                    "follow_up_prompt": "Who is responsible for the AI outcome?",
                }
            )
        ]
    )

    response = PersonaService(llm_client=client).respond(evaluator, meter_after=82)

    assert response.npc_state == "defensive"
    assert response.follow_up_prompt is not None
    assert "accountability" in response.npc_response
    assert "Retrieved evidence" not in str(client.calls[0]["prompt"])
    assert "Earlier private history" not in str(client.calls[0]["prompt"])
    assert "conversation_context" not in str(client.calls[0]["prompt"])
