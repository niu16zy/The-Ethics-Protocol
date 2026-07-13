from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.schemas.evaluator import EvaluatorResult, EvidenceRef


@dataclass(frozen=True)
class PersuasionTarget:
    target_id: str
    label: str
    principles: list[str]
    evidence_document_ids: set[int]
    evidence_terms_any: list[str]
    player_terms_any: list[str]


@dataclass(frozen=True)
class PersuasionHit:
    target: PersuasionTarget
    evidence_refs: list[EvidenceRef]


class LevelPersuasionService:
    def __init__(self, context_dir: Path | None = None) -> None:
        self.context_dir = context_dir or Path(__file__).resolve().parents[1] / "config" / "level_contexts"

    def apply(
        self,
        *,
        level_id: int,
        meter_before: int,
        player_input: str,
        retrieved_refs: list[EvidenceRef],
        evaluator: EvaluatorResult,
        prior_turns: list[Any],
    ) -> EvaluatorResult:
        persuasion = self._load_persuasion_config(level_id)
        if not persuasion or not persuasion.get("enabled", False):
            return evaluator
        if persuasion.get("mode") != "cumulative_all_targets":
            return evaluator
        if not persuasion.get("collapse_meter_on_complete", False):
            return evaluator
        if evaluator.verdict in {"unsupported", "off_topic"}:
            return evaluator

        targets = self._targets_from_config(persuasion)
        if not targets:
            return evaluator

        target_ids = {target.target_id for target in targets}
        prior_hits = self._hits_from_prior_turns(prior_turns, targets)
        current_hits = self._hits_for_turn(player_input, retrieved_refs, targets)
        if not current_hits:
            return evaluator

        new_hits = {
            target_id: hit
            for target_id, hit in current_hits.items()
            if target_id not in prior_hits
        }
        if not new_hits:
            return self._repeated_target_result(evaluator, current_hits)

        combined_hits = {**prior_hits, **current_hits}
        if not target_ids.issubset(combined_hits):
            return evaluator

        matched_current_refs = self._dedupe_refs(
            ref
            for hit in current_hits.values()
            for ref in hit.evidence_refs
        )
        if not matched_current_refs:
            return evaluator

        matched_targets = [
            target
            for target in targets
            if target.target_id in combined_hits
        ]
        target_labels = [target.label for target in matched_targets]
        principles = self._merge_strings(
            evaluator.identified_principles,
            [
                principle
                for target in matched_targets
                for principle in target.principles
            ],
        )

        return evaluator.model_copy(
            update={
                "match_score": max(evaluator.match_score, 0.95),
                "score_delta": -meter_before,
                "verdict": "strong",
                "identified_principles": principles,
                "missing_points": [],
                "evidence_refs": matched_current_refs,
                "reasoning_summary": (
                    "The player has now covered all level-critical knowledge targets "
                    f"across turns: {', '.join(target_labels)}."
                ),
                "persona_instruction": (
                    "NPC should fully concede because the player connected all level-critical "
                    "knowledge targets to retrieved course evidence across turns."
                ),
                "confidence": max(evaluator.confidence, 0.9),
            }
        )

    def _repeated_target_result(
        self,
        evaluator: EvaluatorResult,
        current_hits: dict[str, PersuasionHit],
    ) -> EvaluatorResult:
        target_labels = [hit.target.label for hit in current_hits.values()]
        return evaluator.model_copy(
            update={
                "score_delta": 0,
                "reasoning_summary": (
                    f"{evaluator.reasoning_summary} This argument repeats an already credited "
                    f"level knowledge target: {', '.join(target_labels)}. Repeated knowledge "
                    "targets do not reduce the meter again."
                ),
                "persona_instruction": (
                    "NPC should acknowledge that this point was already credited, then ask the "
                    "player for a different course-grounded weakness."
                ),
            }
        )

    def _load_persuasion_config(self, level_id: int) -> dict[str, Any]:
        path = self.context_dir / f"level_{level_id}_victor_barrett.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        persuasion = data.get("persuasion")
        return persuasion if isinstance(persuasion, dict) else {}

    def _targets_from_config(self, persuasion: dict[str, Any]) -> list[PersuasionTarget]:
        raw_targets = persuasion.get("targets")
        if not isinstance(raw_targets, list):
            return []

        targets: list[PersuasionTarget] = []
        for raw_target in raw_targets:
            if not isinstance(raw_target, dict):
                continue
            target_id = self._clean_string(raw_target.get("id"))
            label = self._clean_string(raw_target.get("label")) or target_id
            player_terms = self._string_list(raw_target.get("player_terms_any"))
            if not target_id or not player_terms:
                continue
            targets.append(
                PersuasionTarget(
                    target_id=target_id,
                    label=label,
                    principles=self._string_list(raw_target.get("principles")),
                    evidence_document_ids=self._int_set(raw_target.get("evidence_document_ids")),
                    evidence_terms_any=self._string_list(raw_target.get("evidence_terms_any")),
                    player_terms_any=player_terms,
                )
            )
        return targets

    def _hits_from_prior_turns(
        self,
        prior_turns: list[Any],
        targets: list[PersuasionTarget],
    ) -> dict[str, PersuasionHit]:
        hits: dict[str, PersuasionHit] = {}
        for row in prior_turns:
            if not self._is_scored_turn(row):
                continue
            player_input = self._row_value(row, "player_input")
            if not isinstance(player_input, str):
                continue
            refs = self._retrieved_refs_from_row(row)
            hits.update(self._hits_for_turn(player_input, refs, targets))
        return hits

    def _hits_for_turn(
        self,
        player_input: str,
        refs: list[EvidenceRef],
        targets: list[PersuasionTarget],
    ) -> dict[str, PersuasionHit]:
        normalized_input = player_input.lower()
        hits: dict[str, PersuasionHit] = {}
        for target in targets:
            if not self._contains_any(normalized_input, target.player_terms_any):
                continue
            matched_refs = [
                ref
                for ref in refs
                if self._evidence_matches(ref, target)
            ]
            if matched_refs:
                hits[target.target_id] = PersuasionHit(
                    target=target,
                    evidence_refs=matched_refs,
                )
        return hits

    def _evidence_matches(self, ref: EvidenceRef, target: PersuasionTarget) -> bool:
        if ref.document_id in target.evidence_document_ids:
            return True
        text = f"{ref.topic or ''} {ref.excerpt}".lower()
        return self._contains_any(text, target.evidence_terms_any)

    def _retrieved_refs_from_row(self, row: Any) -> list[EvidenceRef]:
        raw_refs = self._row_value(row, "retrieved_refs")
        if not isinstance(raw_refs, str):
            return []
        try:
            data = json.loads(raw_refs)
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []

        refs: list[EvidenceRef] = []
        for item in data:
            try:
                refs.append(EvidenceRef.model_validate(item))
            except ValueError:
                continue
        return refs

    def _is_scored_turn(self, row: Any) -> bool:
        value = self._row_value(row, "is_scored")
        if value is None:
            return True
        return bool(value)

    def _row_value(self, row: Any, key: str) -> Any:
        if isinstance(row, dict):
            return row.get(key)
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return None

    def _contains_any(self, text: str, terms: list[str]) -> bool:
        return any(term.lower() in text for term in terms)

    def _dedupe_refs(self, refs: Any) -> list[EvidenceRef]:
        deduped: list[EvidenceRef] = []
        seen: set[tuple[int, int | None]] = set()
        for ref in refs:
            key = (ref.document_id, ref.seq_order)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(ref)
        return deduped

    def _merge_strings(self, first: list[str], second: list[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for value in [*first, *second]:
            normalized = value.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            merged.append(normalized)
        return merged

    def _string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [
            item.strip().lower()
            for item in value
            if isinstance(item, str) and item.strip()
        ]

    def _int_set(self, value: Any) -> set[int]:
        if not isinstance(value, list):
            return set()
        ids: set[int] = set()
        for item in value:
            if isinstance(item, int):
                ids.add(item)
            elif isinstance(item, str) and item.isdigit():
                ids.add(int(item))
        return ids

    def _clean_string(self, value: Any) -> str:
        return value.strip() if isinstance(value, str) else ""
