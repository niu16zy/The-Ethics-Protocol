from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


Verdict = Literal["strong", "partial", "weak", "unsupported", "off_topic"]


class EvidenceRef(BaseModel):
    document_id: int
    course: str | None = None
    lesson: str | None = None
    topic: str | None = None
    seq_order: int | None = None
    excerpt: str
    score: float | None = None


class EvaluatorResult(BaseModel):
    match_score: float = Field(ge=0.0, le=1.0)
    score_delta: int
    verdict: Verdict
    identified_principles: list[str]
    misconceptions_addressed: list[str]
    missing_points: list[str]
    evidence_refs: list[EvidenceRef]
    reasoning_summary: str
    persona_instruction: str
    confidence: float = Field(ge=0.0, le=1.0)
    conversation_context: dict[str, object] | None = None

    @model_validator(mode="after")
    def require_evidence_for_supported_verdicts(self) -> "EvaluatorResult":
        if self.verdict in {"strong", "partial"} and not self.evidence_refs:
            raise ValueError("strong and partial verdicts require evidence_refs")
        return self


class PersonaResponse(BaseModel):
    npc_response: str
    npc_state: Literal["confident", "defensive", "hesitant", "clarifying"]
    follow_up_prompt: str | None = None
