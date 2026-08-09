"""EQ1: retrieval quality on vocabulary-aligned vs paraphrased queries.

Runs the paired query set in queries_v1_v2.json through the real retrieval
service and reports Hit@3, Precision@3, Recall@3 and MRR for each variant.
The headline figure is the drop from v1 (course vocabulary) to v2 (same
argument, course vocabulary avoided), which is what Section 4.3 of the report
claims should be small for this corpus.

No LLM calls: this is deterministic and can be re-run freely.

    python -m evaluation.run_retrieval_eval
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from backend.app.api.dependencies import retrieval_service

TOP_K = 3
HERE = Path(__file__).parent
RESULTS_DIR = HERE / "results"

# v2 is the headline comparison against v1. v2_adversarial is the first version
# of the paraphrase set, which stripped domain vocabulary entirely; it is kept
# so that the sensitivity of the result to paraphrase style stays reproducible.
VARIANTS = ("v1", "v2", "v2_adversarial")


def score_case(retrieved_ids: list[int], relevant: set[int]) -> dict[str, float]:
    """Standard rank metrics for one query against one relevance set."""
    matched = [doc_id for doc_id in retrieved_ids if doc_id in relevant]
    first_rank = next(
        (i + 1 for i, doc_id in enumerate(retrieved_ids) if doc_id in relevant),
        None,
    )
    return {
        "hit_at_k": 1.0 if matched else 0.0,
        "precision_at_k": len(matched) / TOP_K,
        # Recall is capped at TOP_K: a target with 11 relevant documents cannot
        # have them all returned in a 3-document window, so the uncapped figure
        # would understate performance for no useful reason.
        "recall_at_k": len(matched) / min(len(relevant), TOP_K),
        "mrr": 1.0 / first_rank if first_rank else 0.0,
    }


def mean(values: list[float]) -> float:
    return round(statistics.fmean(values), 4) if values else 0.0


def aggregate(rows: list[dict[str, Any]], variant: str) -> dict[str, float]:
    subset = [r for r in rows if r["variant"] == variant]
    return {
        metric: mean([r["metrics"][metric] for r in subset])
        for metric in ("hit_at_k", "precision_at_k", "recall_at_k", "mrr")
    }


def main() -> None:
    payload = json.loads((HERE / "queries_v1_v2.json").read_text(encoding="utf-8"))
    cases = payload["cases"]
    service = retrieval_service()

    rows: list[dict[str, Any]] = []
    for case in cases:
        relevant = set(case["relevant_docs"])
        for variant in VARIANTS:
            if variant not in case:
                continue
            evidence = service.retrieve(case[variant], top_k=TOP_K)
            retrieved_ids = [ref.document_id for ref in evidence]
            rows.append(
                {
                    "id": case["id"],
                    "level": case["level"],
                    "target_id": case["target_id"],
                    "variant": variant,
                    "query": case[variant],
                    "retrieved": retrieved_ids,
                    "relevant": sorted(relevant),
                    "metrics": score_case(retrieved_ids, relevant),
                }
            )

    per_variant = {variant: aggregate(rows, variant) for variant in VARIANTS}
    v1, v2 = per_variant["v1"], per_variant["v2"]
    summary = {
        "queries_per_variant": len(cases),
        "top_k": TOP_K,
        "variants": per_variant,
        "delta_v1_minus_v2": {
            metric: round(v1[metric] - v2[metric], 4) for metric in v1
        },
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "eq1_retrieval.json").write_text(
        json.dumps({"summary": summary, "per_query": rows}, indent=2),
        encoding="utf-8",
    )

    print(f"EQ1 retrieval evaluation -- {len(cases)} queries per variant, top_k={TOP_K}\n")
    header = (
        f"{'metric':<16}{'v1 (course)':>14}{'v2 (student)':>15}"
        f"{'delta':>9}{'v2 adversarial':>17}"
    )
    print(header)
    print("-" * len(header))
    for metric in ("hit_at_k", "precision_at_k", "recall_at_k", "mrr"):
        print(
            f"{metric:<16}{v1[metric]:>14.4f}{v2[metric]:>15.4f}"
            f"{summary['delta_v1_minus_v2'][metric]:>9.4f}"
            f"{per_variant['v2_adversarial'][metric]:>17.4f}"
        )

    for variant in VARIANTS:
        misses = [
            r for r in rows if r["variant"] == variant and r["metrics"]["hit_at_k"] == 0.0
        ]
        print(f"\n{variant}: {len(misses)}/{len(cases)} queries returned no relevant document")
        for row in misses:
            print(f"    {row['id']}: {row['query'][:66]}")

    print(f"\nWritten to {RESULTS_DIR / 'eq1_retrieval.json'}")


if __name__ == "__main__":
    main()
