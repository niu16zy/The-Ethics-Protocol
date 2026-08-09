"""EQ6: where does the time in a turn actually go?

Times the three phases of a debate turn separately -- retrieval, evaluation
and dialogue generation -- over a number of runs, and reports median and 95th
percentile for each.

The phases are driven directly rather than through DebateOrchestrator, because
the orchestrator has no timing hooks and adding them for the sake of a
measurement would change the code being measured.

Runs in whatever mode the environment is configured for. With no provider key
the evaluation and persona phases use their rule-based paths, which measures
system overhead rather than model latency; with a provider configured it
measures the real thing. The mode is recorded in the output either way.

    python -m evaluation.run_latency
    python -m evaluation.run_latency --runs 30
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

from backend.app.api.dependencies import llm_client, retrieval_service
from backend.app.core.config import get_settings
from backend.app.services.conversation_context_service import ConversationContextService
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.persona_service import PersonaService

HERE = Path(__file__).parent
RESULTS_DIR = HERE / "results"


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(int(round(fraction * (len(ordered) - 1))), len(ordered) - 1)
    return ordered[index]


def summarise(samples: list[float]) -> dict[str, float]:
    return {
        "median_ms": round(statistics.median(samples) * 1000, 2),
        "p95_ms": round(percentile(samples, 0.95) * 1000, 2),
        "min_ms": round(min(samples) * 1000, 2),
        "max_ms": round(max(samples) * 1000, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args()

    settings = get_settings()
    client = llm_client()
    provider = settings.llm_provider if client else "rules"

    retrieval = retrieval_service()
    context_service = ConversationContextService()
    evaluation = EvaluationService(llm_client=client, max_attempts=settings.llm_max_attempts)
    persona = PersonaService(llm_client=client, max_attempts=settings.llm_max_attempts)

    cases = json.loads((HERE / "queries_v1_v2.json").read_text(encoding="utf-8"))["cases"]
    timings: dict[str, list[float]] = {"retrieval": [], "evaluation": [], "persona": []}

    print(f"EQ6 latency -- provider={provider}, runs={args.runs}")
    for i in range(args.runs):
        case = cases[i % len(cases)]
        argument = case["v1"]

        # Empty history: this measures a first turn, which is the cheapest
        # case for the context step and isolates retrieval itself.
        empty_context = context_service.build_context([])

        start = time.perf_counter()
        query = context_service.build_retrieval_query(argument, empty_context)
        evidence = retrieval.retrieve(query)
        timings["retrieval"].append(time.perf_counter() - start)

        start = time.perf_counter()
        result = evaluation.evaluate(argument, evidence, None)
        timings["evaluation"].append(time.perf_counter() - start)

        start = time.perf_counter()
        persona.respond(result, 60, argument, dialogue_history={}, level_id=case["level"])
        timings["persona"].append(time.perf_counter() - start)

    per_phase = {phase: summarise(samples) for phase, samples in timings.items()}
    totals = [
        timings["retrieval"][i] + timings["evaluation"][i] + timings["persona"][i]
        for i in range(args.runs)
    ]
    per_phase["total_turn"] = summarise(totals)

    payload = {
        "provider": provider,
        "runs": args.runs,
        "note": (
            "Rule-based paths measure system overhead only; they are not a "
            "prediction of latency with a model provider configured."
            if provider == "rules"
            else "Measured against a live provider."
        ),
        "phases": per_phase,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "eq6_latency.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    header = f"\n{'phase':<14}{'median (ms)':>14}{'p95 (ms)':>12}{'max (ms)':>12}"
    print(header)
    print("-" * len(header.strip()))
    for phase in ("retrieval", "evaluation", "persona", "total_turn"):
        row = per_phase[phase]
        print(f"{phase:<14}{row['median_ms']:>14.2f}{row['p95_ms']:>12.2f}{row['max_ms']:>12.2f}")

    share = per_phase["retrieval"]["median_ms"] / max(per_phase["total_turn"]["median_ms"], 1e-9)
    print(f"\nRetrieval is {share:.1%} of median turn time.")
    print(f"Written to {RESULTS_DIR / 'eq6_latency.json'}")


if __name__ == "__main__":
    main()
