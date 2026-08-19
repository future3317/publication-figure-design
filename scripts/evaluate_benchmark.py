#!/usr/bin/env python3
"""Compute retrieval and generation metrics for the small golden benchmark."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    return 1.0 if relevant.intersection(ranked[:k]) else 0.0


def _ndcg_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    dcg = sum(1.0 / math.log2(index + 2) for index, ref_id in enumerate(ranked[:k]) if ref_id in relevant)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    return dcg / idcg if idcg else 0.0


def evaluate(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks = payload.get("tasks", [])
    retrieval = []
    for task in tasks:
        ranked = [str(value) for value in task.get("ranked_ids", [])]
        relevant = {str(value) for value in task.get("relevant_ids", [])}
        retrieval.append({
            "id": task.get("id"),
            "role": task.get("role"),
            "recall_at_1": _recall_at_k(ranked, relevant, 1),
            "recall_at_3": _recall_at_k(ranked, relevant, 3),
            "ndcg_at_3": round(_ndcg_at_k(ranked, relevant, 3), 6),
        })
    generation = payload.get("generation", [])
    metric_names = ("reference_alignment", "aesthetic", "scientific", "export")
    averages = {
        name: round(sum(float(row.get(name, 0.0)) for row in generation) / len(generation), 6) if generation else 0.0
        for name in metric_names
    }
    return {
        "schema_version": "1.0",
        "benchmark": str(path),
        "retrieval": retrieval,
        "retrieval_summary": {
            "recall_at_1": round(sum(row["recall_at_1"] for row in retrieval) / len(retrieval), 6) if retrieval else 0.0,
            "recall_at_3": round(sum(row["recall_at_3"] for row in retrieval) / len(retrieval), 6) if retrieval else 0.0,
            "ndcg_at_3": round(sum(row["ndcg_at_3"] for row in retrieval) / len(retrieval), 6) if retrieval else 0.0,
        },
        "generation_summary": averages,
        "golden_task_count": len(tasks),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=root / "assets" / "reference-benchmarks" / "golden_tasks.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.benchmark)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
