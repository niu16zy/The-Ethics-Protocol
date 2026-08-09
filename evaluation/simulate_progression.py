"""EQ5: does the cumulative persuasion design behave as Section 4.7 claims?

Section 4.7 argues that a player cannot finish a level by repeating one good
argument, because the meter only collapses once every persuasion target for
that level has been hit. This script tests that claim directly by driving the
real DebateOrchestrator through four scenarios on each level:

    A  full path      -- hit every target in order; the meter should collapse
                         only on the final one
    B  repetition     -- submit one strong argument ten times; the meter must
                         not collapse
    C  partial        -- hit every target but one; the meter must not collapse
    D  reordered      -- hit every target in reverse order; the outcome should
                         match scenario A

Runs against a temporary database in rules-only mode, so it is deterministic
and needs no API key.

    python -m evaluation.simulate_progression
"""

from __future__ import annotations

import json
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from backend.app.repositories.app_repository import AppRepository
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.evaluator import EvaluatorResult, EvidenceRef
from backend.app.schemas.user import UserCreate
from backend.app.services.conversation_context_service import ConversationContextService
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.level_persuasion_service import LevelPersuasionService
from backend.app.services.meter_service import MeterService
from backend.app.services.orchestrator_service import DebateOrchestrator
from backend.app.services.persona_service import PersonaService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.core.config import get_settings

HERE = Path(__file__).parent
RESULTS_DIR = HERE / "results"
INITIAL_METER = 100


class FixedVerdictEvaluationService:
    """Stub evaluator returning a constant scoreable verdict.

    The claim under test in this experiment belongs to the persuasion layer,
    not the evaluator. Holding the verdict constant removes evaluator quality
    as a confound, so that any change in meter behaviour can only come from
    the cumulative target logic. The real evaluator is exercised separately in
    the rules-only completability check below.
    """

    last_source = "stub"

    def evaluate(
        self,
        player_input: str,
        evidence: list[EvidenceRef],
        conversation_context: Any = None,
    ) -> EvaluatorResult:
        return EvaluatorResult(
            match_score=0.7,
            score_delta=-20,
            verdict="partial",
            identified_principles=["accountability"],
            misconceptions_addressed=[],
            missing_points=["Connect the remaining control."],
            evidence_refs=evidence,
            reasoning_summary="Fixed verdict used for progression testing.",
            persona_instruction="Acknowledge the point under pressure.",
            confidence=0.7,
        )


def load_arguments_by_target() -> dict[tuple[int, str], list[str]]:
    """Reuse the vocabulary-aligned queries from EQ1 as known-good arguments."""
    payload = json.loads((HERE / "queries_v1_v2.json").read_text(encoding="utf-8"))
    grouped: dict[tuple[int, str], list[str]] = defaultdict(list)
    for case in payload["cases"]:
        grouped[(case["level"], case["target_id"])].append(case["v1"])
    return grouped


def build_orchestrator(
    db_path: Path, *, stub_evaluator: bool
) -> tuple[DebateOrchestrator, AppRepository]:
    """Orchestrator with no LLM client anywhere, so runs are deterministic."""
    settings = get_settings()
    repository = AppRepository(db_path)
    repository.initialize()
    knowledge = KnowledgeRepository(settings.knowledge_db_path)
    evaluation = FixedVerdictEvaluationService() if stub_evaluator else EvaluationService()
    orchestrator = DebateOrchestrator(
        app_repository=repository,
        retrieval_service=RetrievalService(knowledge, settings.default_top_k),
        evaluation_service=evaluation,  # type: ignore[arg-type]
        persona_service=PersonaService(),
        meter_service=MeterService(),
        conversation_context_service=ConversationContextService(),
        level_persuasion_service=LevelPersuasionService(),
    )
    return orchestrator, repository


def run_sequence(
    db_path: Path, level: int, arguments: list[str], *, stub_evaluator: bool = True
) -> list[dict[str, Any]]:
    orchestrator, repository = build_orchestrator(db_path, stub_evaluator=stub_evaluator)
    user = repository.create_user(
        UserCreate(username=f"eq5-l{level}", display_name=f"EQ5 level {level}")
    )
    session = repository.create_session(user.id, level, INITIAL_METER)

    trace: list[dict[str, Any]] = []
    for argument in arguments:
        response = orchestrator.submit_turn(session.id, argument)
        trace.append(
            {
                "argument": argument,
                "verdict": response.evaluator.verdict,
                "score_delta": response.score_delta,
                "meter_before": response.meter_before,
                "meter_after": response.meter_after,
            }
        )
    return trace


def targets_for_level(by_target: dict[tuple[int, str], list[str]], level: int) -> list[str]:
    return [target for (lvl, target) in by_target if lvl == level]


def check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}: {detail}")
    return {"scenario": name, "passed": passed, "detail": detail}


def main() -> None:
    by_target = load_arguments_by_target()
    results: list[dict[str, Any]] = []

    # ignore_cleanup_errors: on Windows the SQLite files stay locked briefly
    # after the last connection closes, which would otherwise raise here.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp_dir = Path(tmp)

        for level in (1, 2, 3):
            targets = targets_for_level(by_target, level)
            print(f"\nLevel {level} -- {len(targets)} persuasion targets")

            # A: one argument per target, in declaration order.
            full = [by_target[(level, t)][0] for t in targets]
            trace_a = run_sequence(tmp_dir / f"a{level}.db", level, full)
            collapsed_at = next(
                (i for i, step in enumerate(trace_a) if step["meter_after"] == 0), None
            )
            results.append(
                check(
                    f"L{level}-A-full-path",
                    collapsed_at == len(full) - 1,
                    f"meter reached 0 at turn {collapsed_at} of {len(full) - 1} "
                    f"(trace: {[s['meter_after'] for s in trace_a]})",
                )
            )

            # B: the same strong argument ten times.
            repeated = [full[0]] * 10
            trace_b = run_sequence(tmp_dir / f"b{level}.db", level, repeated)
            results.append(
                check(
                    f"L{level}-B-repetition",
                    all(step["meter_after"] > 0 for step in trace_b),
                    f"final meter {trace_b[-1]['meter_after']} after 10 repeats "
                    f"(deltas: {sorted({s['score_delta'] for s in trace_b})})",
                )
            )

            # C: every target but the last.
            if len(full) > 1:
                trace_c = run_sequence(tmp_dir / f"c{level}.db", level, full[:-1])
                results.append(
                    check(
                        f"L{level}-C-partial",
                        all(step["meter_after"] > 0 for step in trace_c),
                        f"final meter {trace_c[-1]['meter_after']} with "
                        f"{len(full) - 1}/{len(full)} targets hit",
                    )
                )

            # D: reverse order.
            trace_d = run_sequence(tmp_dir / f"d{level}.db", level, list(reversed(full)))
            collapsed_d = next(
                (i for i, step in enumerate(trace_d) if step["meter_after"] == 0), None
            )
            results.append(
                check(
                    f"L{level}-D-reordered",
                    collapsed_d == len(full) - 1,
                    f"meter reached 0 at turn {collapsed_d} of {len(full) - 1} "
                    "(order should not matter)",
                )
            )

    passed = sum(1 for r in results if r["passed"])

    # Secondary check, with the stub removed: can the game actually be finished
    # when the rule-based fallback evaluator is doing the grading, as it does
    # when no provider is configured?
    print("\nRules-only completability (real fallback evaluator, no stub)")
    rules_only: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp_dir = Path(tmp)
        for level in (1, 2, 3):
            targets = targets_for_level(by_target, level)
            full = [by_target[(level, t)][0] for t in targets]
            trace = run_sequence(
                tmp_dir / f"r{level}.db", level, full, stub_evaluator=False
            )
            verdicts = [step["verdict"] for step in trace]
            completed = trace[-1]["meter_after"] == 0
            unsupported = sum(1 for v in verdicts if v in {"unsupported", "off_topic"})
            rules_only.append(
                {
                    "level": level,
                    "completed": completed,
                    "verdicts": verdicts,
                    "unscored_targets": unsupported,
                    "final_meter": trace[-1]["meter_after"],
                }
            )
            print(
                f"  Level {level}: completed={completed}, final meter "
                f"{trace[-1]['meter_after']}, {unsupported}/{len(full)} target "
                f"arguments graded unsupported ({verdicts})"
            )

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "eq5_progression.json").write_text(
        json.dumps(
            {
                "passed": passed,
                "total": len(results),
                "scenarios": results,
                "rules_only_completability": rules_only,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n{passed}/{len(results)} controlled scenarios passed")
    print(f"Written to {RESULTS_DIR / 'eq5_progression.json'}")


if __name__ == "__main__":
    main()
