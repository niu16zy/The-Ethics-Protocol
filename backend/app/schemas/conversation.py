from __future__ import annotations

from pydantic import BaseModel, Field


class ConversationTurnSummary(BaseModel):
    turn_index: int
    player_input_summary: str
    verdict: str | None = None
    identified_principles: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    reasoning_summary: str | None = None


class ConversationContext(BaseModel):
    recent_turns: list[ConversationTurnSummary] = Field(default_factory=list)
    carryover_terms: list[str] = Field(default_factory=list)
    unresolved_principles: list[str] = Field(default_factory=list)
    unresolved_missing_points: list[str] = Field(default_factory=list)

    @property
    def has_history(self) -> bool:
        return bool(self.recent_turns)
