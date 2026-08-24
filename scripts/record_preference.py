#!/usr/bin/env python3
"""Append a pairwise preference observation to the canonical dataset.

The legacy ``left/right/winner`` fields remain for benchmark readers, while
``preferred/rejected/reason_codes`` are the canonical human-review fields.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REASON_CODES = {
    "layout",
    "hierarchy",
    "spacing",
    "typography",
    "palette",
    "annotation",
    "data_clarity",
    "overall_polish",
}
REASON_ALIASES = {
    "whitespace": "spacing",
    "professional_finish": "overall_polish",
    "palette_discipline": "palette",
    "annotation_clearance": "annotation",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left_id")
    parser.add_argument("right_id")
    parser.add_argument("winner", choices=["left", "right"])
    parser.add_argument("--reason", "--reason-code", dest="reason", action="append", default=[])
    parser.add_argument("--figure-family", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--candidate-kind", choices=["reference", "candidate"], default="candidate")
    parser.add_argument("--candidate-id", action="append", default=[], help="repeat exactly three times for the A/B/C candidate set")
    parser.add_argument("--reviewer", default="auto_visual_judge")
    parser.add_argument("--notes", default="")
    parser.add_argument("--status", choices=["champion", "challenger", "rejected"], default="challenger")
    args = parser.parse_args()
    reasons = sorted({REASON_ALIASES.get(str(value).strip(), str(value).strip()) for value in args.reason if str(value).strip()})
    if not reasons:
        parser.error("at least one --reason-code is required")
    unsupported = sorted(set(reasons) - REASON_CODES)
    if unsupported:
        parser.error("unsupported --reason-code: " + ", ".join(unsupported) + "; use the canonical eight codes")
    candidate_ids = [str(value).strip() for value in args.candidate_id if str(value).strip()]
    if candidate_ids and (len(candidate_ids) != 3 or args.left_id not in candidate_ids or args.right_id not in candidate_ids):
        parser.error("--candidate-id must be supplied exactly three times and include both positional candidate ids")
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
        "candidate_ids": candidate_ids,
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
