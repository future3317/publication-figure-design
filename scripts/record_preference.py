#!/usr/bin/env python3
"""Append a pairwise preference observation to the canonical dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left_id")
    parser.add_argument("right_id")
    parser.add_argument("winner", choices=["left", "right"])
    parser.add_argument("--reason", action="append", default=[])
    parser.add_argument("--figure-family", default="")
    parser.add_argument("--status", choices=["champion", "challenger", "rejected"], default="challenger")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    path = root / "assets" / "reference-benchmarks" / "preference_pairs.jsonl"
    winner = args.left_id if args.winner == "left" else args.right_id
    row = {"left_id": args.left_id, "right_id": args.right_id, "winner": winner, "reasons": args.reason, "figure_family": args.figure_family, "status": args.status}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
