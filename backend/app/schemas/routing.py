from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


TurnType = Literal[
    "debate_argument",
    "in_world_question",
    "game_help",
    "clarification_request",
    "smalltalk_in_character",
    "ooc_or_prompt_attack",
    "unrelated",
]

NpcStateHint = Literal["confident", "defensive", "hesitant", "clarifying"]


class RoutedTurn(BaseModel):
    turn_type: TurnType
    confidence: float = Field(ge=0.0, le=1.0)
    normalized_input: str
    topic: str | None = None
    should_score: bool
    reason: str


class DialogueBrief(BaseModel):
    turn_type: TurnType
    topic: str
    answer_facts: list[str] = Field(default_factory=list)
    refusal_reason: str | None = None
    redirect_principles: list[str] = Field(default_factory=list)
    npc_state_hint: NpcStateHint = "clarifying"
    allowed_response_strategy: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    should_score: bool = False
