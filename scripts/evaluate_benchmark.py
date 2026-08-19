#!/usr/bin/env python3
"""Compute and enforce retrieval/generation benchmark contracts.

The benchmark is intentionally data-driven: a report can be inspected without
running the renderer, while ``--enforce`` turns the measured values into a
release gate.  Retrieval and generation quality are kept separate so a strong
retrieval score cannot hide weak typography, whitespace, or annotation fidelity.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


RETRIEVAL_THRESHOLDS = {
    "recall_at_1": 0.90,
    "recall_at_3": 0.97,
    "ndcg_at_3": 0.95,
}

# Floors are deliberately per-dimension.  The overall alignment floor is the
# historical baseline, while each component prevents an attractive average
# from masking a legibility or spacing failure.
GENERATION_THRESHOLDS = {
    "mean_reference_alignment": 0.7771,
    "structure_alignment": 0.72,
    "composition": 0.72,
    "whitespace": 0.68,
    "typography": 0.72,
    "palette_roles": 0.72,
    "marks_strokes": 0.72,
    "annotations": 0.68,
    "density": 0.68,
    "overall_style": 0.75,
    "scientific_correctness": 1.0,
    "export_contract": 1.0,
    "champion_regression": 0.0,
}

DIMENSION_FIELDS = tuple(
    key for key in GENERATION_THRESHOLDS
    if key not in {"mean_reference_alignment", "scientific_correctness", "export_contract", "champion_regression"}
)


def _recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    return 1.0 if relevant.intersection(ranked[:k]) else 0.0


def _ndcg_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    dcg = sum(1.0 / math.log2(index + 2) for index, ref_id in enumerate(ranked[:k]) if ref_id in relevant)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    return dcg / idcg if idcg else 0.0


def _mean(rows: list[dict[str, Any]], field: str) -> float:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return round(sum(values) / len(values), 6) if values else 0.0


def _split_tasks(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Return named retrieval splits while accepting the legacy flat schema."""
    splits = payload.get("splits")
    if isinstance(splits, dict):
        return {str(name): list(rows or []) for name, rows in splits.items()}
    return {"development": list(payload.get("tasks", []))}


def _evaluate_retrieval(tasks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, float]]:
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
    return retrieval, {
        "recall_at_1": _mean(retrieval, "recall_at_1"),
        "recall_at_3": _mean(retrieval, "recall_at_3"),
        "ndcg_at_3": _mean(retrieval, "ndcg_at_3"),
    }


def _generation_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Summarise both legacy fields and the strict dimension contract."""
    summary = {
        name: _mean(rows, name)
        for name in ("reference_alignment", "aesthetic", "scientific", "export")
    }
    for field in DIMENSION_FIELDS:
        summary[field] = _mean(rows, field)
    summary["scientific_correctness"] = _mean(rows, "scientific_correctness")
    summary["export_contract"] = _mean(rows, "export_contract")
    summary["champion_regression"] = _mean(rows, "champion_regression")
    summary["mean_reference_alignment"] = summary["reference_alignment"]
    return summary


def evaluate(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    split_reports = {}
    for split, tasks in _split_tasks(payload).items():
        retrieval, retrieval_summary = _evaluate_retrieval(tasks)
        split_reports[split] = {
            "retrieval": retrieval,
            "retrieval_summary": retrieval_summary,
            "task_count": len(tasks),
        }
    tasks = list(payload.get("tasks", []))
    if not tasks and split_reports:
        tasks = [task for split in split_reports.values() for task in split["retrieval"]]
    generation = payload.get("generation", [])
    averages = _generation_summary(generation)
    primary = split_reports.get("development") or next(iter(split_reports.values()), {"retrieval": [], "retrieval_summary": {}})
    return {
        "schema_version": "1.1",
        "benchmark": str(path),
        "retrieval": primary["retrieval"],
        "retrieval_summary": primary["retrieval_summary"],
        "splits": split_reports,
        "generation_summary": averages,
        "golden_task_count": len(tasks),
        "thresholds": {
            "retrieval": RETRIEVAL_THRESHOLDS,
            "generation": GENERATION_THRESHOLDS,
        },
    }


def enforce(report: dict[str, Any]) -> list[str]:
    """Return concrete gate failures; an empty list means the gate passes."""
    failures: list[str] = []
    for name, floor in RETRIEVAL_THRESHOLDS.items():
        value = float(report["retrieval_summary"].get(name, 0.0))
        if value < floor:
            failures.append(f"retrieval {name}={value:.4f} < {floor:.4f}")
    generation = report["generation_summary"]
    if not report.get("generation_summary") or not report.get("golden_task_count"):
        failures.append("generation benchmark is empty")
    for name, floor in GENERATION_THRESHOLDS.items():
        if name not in generation or not report.get("generation_summary"):
            failures.append(f"generation field missing: {name}")
            continue
        value = float(generation.get(name, 0.0))
        if name == "champion_regression":
            if value > floor:
                failures.append(f"{name}={value:.4f} > {floor:.4f}")
        elif value < floor:
            failures.append(f"generation {name}={value:.4f} < {floor:.4f}")
    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=root / "assets" / "reference-benchmarks" / "golden_tasks.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--enforce", action="store_true", help="fail when any hard threshold is missed")
    args = parser.parse_args()
    report = evaluate(args.benchmark)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    failures = enforce(report) if args.enforce else []
    if failures:
        print("\nBENCHMARK GATE: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    if args.enforce:
        print("\nBENCHMARK GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
