#!/usr/bin/env python3
"""Enforce the fixed generation-regression corpus and blind pairwise report.

The corpus contains task identities and champion floors; generated metrics are
supplied by the renderer run.  Keeping the reports separate lets CI compare a
new render against the stored baseline without exposing the baseline ranking to
the task prompt or retrieval code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(corpus_path: Path, baseline_path: Path | None, candidate_path: Path | None) -> dict[str, Any]:
    corpus = _load(corpus_path)
    tasks = list(corpus.get("tasks", []))
    baseline = _load(baseline_path) if baseline_path and baseline_path.is_file() else None
    candidate = _load(candidate_path) if candidate_path and candidate_path.is_file() else None
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "corpus": str(corpus_path),
        "task_count": len(tasks),
        "required_task_count": int(corpus.get("required_task_count", 20)),
        "baseline_present": baseline is not None,
        "candidate_present": candidate is not None,
        "pairwise": [],
        "failures": [],
    }
    if len(tasks) < report["required_task_count"]:
        report["failures"].append(
            f"corpus has {len(tasks)} tasks; requires {report['required_task_count']}"
        )
        return report
    if baseline is None or candidate is None:
        report["failures"].append("baseline and candidate reports are required for blind pairwise evaluation")
        return report

    baseline_rows = {str(row.get("task_id")): row for row in baseline.get("generation", baseline.get("cases", []))}
    candidate_rows = {str(row.get("task_id", row.get("case_id"))): row for row in candidate.get("generation", candidate.get("cases", []))}
    for task in tasks:
        task_id = str(task.get("id"))
        old = baseline_rows.get(task_id)
        new = candidate_rows.get(task_id)
        if old is None or new is None:
            report["failures"].append(f"missing report row for {task_id}")
            continue
        old_score = float(old.get("overall_style", old.get("reference_alignment", 0.0)))
        new_score = float(new.get("overall_style", new.get("reference_alignment", 0.0)))
        floor = float(task.get("champion_floor", 0.0))
        row = {"task_id": task_id, "baseline": old_score, "candidate": new_score, "delta": round(new_score - old_score, 6)}
        report["pairwise"].append(row)
        if new_score < floor:
            report["failures"].append(f"{task_id}: candidate {new_score:.4f} < champion floor {floor:.4f}")
        if new_score < old_score:
            report["failures"].append(f"{task_id}: candidate regressed by {new_score - old_score:.4f}")
    report["mean_baseline"] = round(sum(row["baseline"] for row in report["pairwise"]) / len(report["pairwise"]), 6) if report["pairwise"] else 0.0
    report["mean_candidate"] = round(sum(row["candidate"] for row in report["pairwise"]) / len(report["pairwise"]), 6) if report["pairwise"] else 0.0
    report["passed"] = not report["failures"]
    return report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=root / "assets" / "reference-benchmarks" / "generation_regression_corpus.json")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--enforce", action="store_true")
    parser.add_argument("--contract-only", action="store_true")
    args = parser.parse_args()
    if args.contract_only:
        corpus = _load(args.corpus)
        report = {"corpus": str(args.corpus), "task_count": len(corpus.get("tasks", [])), "required_task_count": corpus.get("required_task_count", 20), "passed": len(corpus.get("tasks", [])) >= int(corpus.get("required_task_count", 20)), "failures": []}
        if not report["passed"]:
            report["failures"].append("generation corpus is smaller than required")
    else:
        if args.baseline is None or args.candidate is None:
            parser.error("--baseline and --candidate are required unless --contract-only is used")
        report = evaluate(args.corpus, args.baseline, args.candidate)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if args.enforce and report["failures"]:
        for failure in report["failures"]:
            print(f"GENERATION REGRESSION: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
