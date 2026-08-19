#!/usr/bin/env python3
"""Evaluate the separate holdout split without printing expected rankings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evaluate_benchmark import enforce, evaluate


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=root / "assets" / "reference-benchmarks" / "holdout_tasks.json")
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()
    report = evaluate(args.benchmark)
    summary = {
        "split": "hidden_holdout",
        "task_count": report.get("golden_task_count", 0),
        "retrieval_summary": report.get("retrieval_summary", {}),
        "generation_summary": report.get("generation_summary", {}),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if args.enforce:
        failures = enforce(report)
        if failures:
            for failure in failures:
                print(f"HOLDOUT GATE: {failure}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
