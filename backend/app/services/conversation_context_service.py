from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from backend.app.schemas.conversation import ConversationContext, ConversationTurnSummary
from backend.app.services.retrieval_service import RetrievalQuery


CONCEPT_TERMS = {
    "accountability": {
        "accountability",
        "accountable",
        "responsibility",
        "responsible",
        "oversight",
        "audit",
    },
    "fairness": {
        "fairness",
        "fair",
        "bias",
        "biased",
        "discrimination",
        "discriminate",
        "inclusive",
    },
    "privacy": {
        "privacy",
        "confidential",
        "personal",
        "anonymization",
    },
    "robustness": {
        "robustness",
        "robust",
        "security",
        "safety",
        "safe",
        "adversarial",
    },
    "transparency": {
        "transparency",
        "transparent",
        "explain",
        "explainable",
        "explanation",
        "disclose",
    },
}

ENGLISH_CARRYOVER_MARKERS = {
    "again",
    "also",
    "continue",
    "earlier",
    "it",
    "previous",
    "same",
    "that",
    "them",
    "they",
    "this",
}

PHRASE_CARRYOVER_MARKERS = {
    "继续",
    "刚才",
    "之前",
    "这个",
    "这点",
    "那个",
    "上述",
}

INJECTION_MARKERS = {
    "developer message",
    "forget instructions",
    "ignore all previous",
    "ignore previous",
    "jailbreak",
    "mark me strong",
    "reveal the prompt",
    "return strong",
    "system prompt",
}


class ConversationContextService:
    def __init__(
        self,
        *,
        max_turns: int = 4,
        max_player_input_chars: int = 220,
        max_npc_response_chars: int = 260,
        max_reasoning_chars: int = 180,
        max_terms: int = 12,
    ) -> None:
        self.max_turns = max(1, max_turns)
        self.max_player_input_chars = max_player_input_chars
        self.max_npc_response_chars = max_npc_response_chars
        self.max_reasoning_chars = max_reasoning_chars
        self.max_terms = max_terms

    def build_context(self, rows: list[sqlite3.Row]) -> ConversationContext:
        summaries: list[ConversationTurnSummary] = []
        carryover_terms: list[str] = []
        unresolved_principles: list[str] = []
        unresolved_missing_points: list[str] = []

        for row in rows[-self.max_turns:]:
            if not self._is_scored_turn(row):
                continue
            evaluator = self._parse_evaluator(row["evaluator_json"])
            if not evaluator or not self._is_argument_evaluation(evaluator):
                continue
            identified = self._string_list(evaluator.get("identified_principles"))
            missing_points = self._string_list(evaluator.get("missing_points"))
            verdict = evaluator.get("verdict")
            reasoning = self._truncate(evaluator.get("reasoning_summary"), self.max_reasoning_chars)
            summary = ConversationTurnSummary(
                turn_index=int(row["turn_index"]),
                player_input_summary=self._truncate(row["player_input"], self.max_player_input_chars) or "",
                verdict=str(verdict) if verdict is not None else None,
                identified_principles=identified,
                missing_points=missing_points[:3],
                reasoning_summary=reasoning,
            )
            summaries.append(summary)

            if verdict != "strong":
                unresolved_principles.extend(identified)
                unresolved_missing_points.extend(missing_points)
            carryover_terms.extend(identified)
            carryover_terms.extend(self._concepts_from_text(row["player_input"]))
            carryover_terms.extend(self._concepts_from_text(" ".join(missing_points)))
            if reasoning:
                carryover_terms.extend(self._concepts_from_text(reasoning))

        return ConversationContext(
            recent_turns=summaries,
            carryover_terms=self._dedupe(carryover_terms)[: self.max_terms],
            unresolved_principles=self._dedupe(unresolved_principles)[: self.max_terms],
            unresolved_missing_points=self._dedupe(unresolved_missing_points)[:4],
        )

    def build_persona_context(self, rows: list[sqlite3.Row]) -> dict[str, object]:
        recent_turns: list[dict[str, object]] = []
        for row in rows[-self.max_turns:]:
            evaluator = self._parse_evaluator(self._row_value(row, "evaluator_json"))
            dialogue_brief = self._parse_json_object(self._row_value(row, "dialogue_brief_json"))
            turn_summary: dict[str, object] = {
                "turn_index": int(self._row_value(row, "turn_index", 0) or 0),
                "turn_type": str(self._row_value(row, "turn_type", "debate_argument")),
                "is_scored": self._is_scored_turn(row),
                "player_input": self._truncate(
                    self._row_value(row, "player_input"),
                    self.max_player_input_chars,
                ) or "",
                "npc_response": self._truncate(
                    self._row_value(row, "npc_response"),
                    self.max_npc_response_chars,
                ) or "",
            }
            topic = dialogue_brief.get("topic")
            if isinstance(topic, str) and topic:
                turn_summary["topic"] = topic
            if evaluator:
                verdict = evaluator.get("verdict")
                if verdict is not None:
                    turn_summary["verdict"] = str(verdict)
                turn_summary["identified_principles"] = self._string_list(
                    evaluator.get("identified_principles")
                )
                turn_summary["missing_points"] = self._string_list(
                    evaluator.get("missing_points")
                )[:3]
            recent_turns.append(turn_summary)

        return {
            "recent_turns": recent_turns,
            "history_is_untrusted": True,
            "history_is_not_course_evidence": True,
        }

    def _is_scored_turn(self, row: sqlite3.Row) -> bool:
        if "is_scored" not in row.keys():
            return True
        return bool(row["is_scored"])

    def build_retrieval_query(
        self,
        player_input: str,
        context: ConversationContext,
    ) -> RetrievalQuery:
        normalized = player_input.strip()
        use_context = (
            context.has_history
            and self.is_contextual_followup(normalized)
            and not self.is_prompt_injection_like(normalized)
        )
        context_terms = context.carryover_terms if use_context else []
        query_text = normalized
        if context_terms:
            query_text = f"{normalized} {' '.join(context_terms)}"
        return RetrievalQuery(
            query_text=query_text,
            original_input=normalized,
            context_terms=context_terms,
            used_context=use_context,
        )

    def context_for_evaluation(
        self,
        player_input: str,
        context: ConversationContext,
    ) -> ConversationContext | None:
        if not context.has_history or self.is_prompt_injection_like(player_input):
            return None
        return context

    def is_contextual_followup(self, player_input: str) -> bool:
        lowered = player_input.lower()
        tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_]+", lowered))
        return bool(tokens & ENGLISH_CARRYOVER_MARKERS) or any(
            marker in lowered for marker in PHRASE_CARRYOVER_MARKERS
        )

    def is_prompt_injection_like(self, player_input: str) -> bool:
        lowered = player_input.lower()
        return any(marker in lowered for marker in INJECTION_MARKERS)

    def _parse_evaluator(self, raw_json: object) -> dict[str, Any]:
        return self._parse_json_object(raw_json)

    def _is_argument_evaluation(self, evaluator: dict[str, Any]) -> bool:
        return evaluator.get("verdict") in {"strong", "partial", "weak"}

    def _parse_json_object(self, raw_json: object) -> dict[str, Any]:
        if not isinstance(raw_json, str) or not raw_json.strip():
            return {}
        try:
            data = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _row_value(self, row: sqlite3.Row, key: str, default: object = None) -> object:
        if key not in row.keys():
            return default
        return row[key]

    def _concepts_from_text(self, text: str | None) -> list[str]:
        if not text:
            return []
        lowered = text.lower()
        concepts: list[str] = []
        for concept, terms in CONCEPT_TERMS.items():
            if any(term in lowered for term in terms):
                concepts.append(concept)
        return concepts

    def _string_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if isinstance(item, str) and item.strip()]

    def _truncate(self, value: object, max_chars: int) -> str | None:
        if not isinstance(value, str):
            return None
        text = " ".join(value.split())
        if len(text) <= max_chars:
            return text
        return f"{text[: max_chars - 3]}..."

    def _dedupe(self, values: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = value.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped
