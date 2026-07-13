from __future__ import annotations

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
