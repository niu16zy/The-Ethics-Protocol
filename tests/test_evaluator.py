from __future__ import annotations

import json

from backend.app.schemas.evaluator import EvidenceRef
from backend.app.services.evaluation_service import EvaluationService


def test_evaluator_returns_schema_valid_structured_json():
    service = EvaluationService()
    evidence = [
        EvidenceRef(
            document_id=1,
            topic="Pillar: Fairness",
            excerpt="AI should treat individuals or groups equally and counter human biases.",
            seq_order=1,
        )
    ]

    result = service.evaluate(
        "The system is biased and unfair because it can discriminate in hiring.",
        evidence,
    )

    assert result.verdict in {"strong", "partial"}
    assert result.evidence_refs
    assert "fairness" in result.identified_principles
    assert result.score_delta in {-28, -20}


def test_evaluator_calibrates_llm_score_delta_by_verdict():
    evidence = [
        EvidenceRef(
            document_id=1,
            topic="Pillar: Fairness",
            excerpt="AI should treat individuals or groups equally and counter human biases.",
            seq_order=1,
        )
    ]

    class ClientWithSmallDelta:
        def generate_text(
            self,
            prompt: str,
            *,
            temperature: float,
            response_mime_type: str | None = None,
        ) -> str:
            return json.dumps(
                {
                    "match_score": 0.72,
                    "score_delta": -5,
                    "verdict": "partial",
                    "identified_principles": ["fairness"],
                    "misconceptions_addressed": [],
                    "missing_points": ["Explain accountability."],
                    "evidence_refs": [evidence[0].model_dump()],
                    "reasoning_summary": "The argument is partly grounded.",
                    "persona_instruction": "Partly concede and ask for accountability.",
                    "confidence": 0.7,
                }
            )

    result = EvaluationService(llm_client=ClientWithSmallDelta()).evaluate(
        "The system is unfair because biased hiring data can discriminate.",
        evidence,
    )

    assert result.verdict == "partial"
    assert result.score_delta == -20


def test_invalid_json_fallback_is_low_confidence():
    service = EvaluationService()

    result = service.parse_or_fallback("{not-json", evidence=[])

    assert result.verdict == "unsupported"
    assert result.confidence == 0.0
    assert result.score_delta == 0


def test_low_confidence_path_when_no_evidence():
    service = EvaluationService()

    result = service.evaluate("This argument has no retrieval support.", evidence=[])

    assert result.verdict == "unsupported"
    assert result.evidence_refs == []
    assert result.score_delta == 0


def test_question_like_input_is_not_scored_by_rule_fallback_even_with_evidence():
    evidence = [
        EvidenceRef(
            document_id=1,
            topic="Pillar: Fairness",
            excerpt="Fair AI tools are designed to minimize bias and discrimination.",
            seq_order=1,
        )
    ]

    result = EvaluationService().evaluate("What is AI fairness?", evidence)

    assert result.verdict == "unsupported"
    assert result.score_delta == 0
    assert result.confidence < 0.5
