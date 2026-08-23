#!/usr/bin/env python3
"""Append a pairwise preference observation to the canonical dataset.

The legacy ``left/right/winner`` fields remain for benchmark readers, while
``preferred/rejected/reason_codes`` are the canonical human-review fields.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left_id")
    parser.add_argument("right_id")
    parser.add_argument("winner", choices=["left", "right"])
    parser.add_argument("--reason", "--reason-code", dest="reason", action="append", default=[])
    parser.add_argument("--figure-family", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--candidate-kind", choices=["reference", "candidate"], default="candidate")
    parser.add_argument("--reviewer", default="human")
    parser.add_argument("--notes", default="")
    parser.add_argument("--status", choices=["champion", "challenger", "rejected"], default="challenger")
    args = parser.parse_args()
    reasons = sorted({str(value).strip() for value in args.reason if str(value).strip()})
    if not reasons:
        parser.error("at least one --reason-code is required")
    root = Path(__file__).resolve().parents[1]
    path = root / "assets" / "reference-benchmarks" / "preference_pairs.jsonl"
    winner = args.left_id if args.winner == "left" else args.right_id
    rejected = args.right_id if winner == args.left_id else args.left_id
    row = {
        "left_id": args.left_id,
        "right_id": args.right_id,
        "winner": winner,
        "preferred": winner,
        "rejected": rejected,
        "reasons": reasons,
        "reason_codes": reasons,
        "figure_family": args.figure_family,
        "task_id": args.task_id,
        "candidate_kind": args.candidate_kind,
        "reviewer": args.reviewer,
        "notes": args.notes,
        "status": args.status,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
