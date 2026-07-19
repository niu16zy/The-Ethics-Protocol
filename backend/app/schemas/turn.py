from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.schemas.evaluator import EvaluatorResult, EvidenceRef


class DebateTurnCreate(BaseModel):
    player_input: str = Field(min_length=1, max_length=4000)


class DebateTurnResponse(BaseModel):
    session_id: int
    turn_index: int
    player_input: str
    retrieved_refs: list[EvidenceRef]
    evaluator: EvaluatorResult
    npc_response: str
    meter_before: int
    meter_after: int
    score_delta: int
    evaluator_source: str | None = None
    persona_source: str | None = None
