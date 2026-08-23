#!/usr/bin/env python3
"""Evaluate should-trigger/should-not-trigger activation datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate(path: Path) -> dict:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    failures = []
    for row in rows:
        expected = bool(row.get("should_trigger"))
        observed = bool(row.get("expected_route"))
        if expected != observed:
            failures.append(row.get("id", "unknown"))
    return {"split": path.stem, "count": len(rows), "failures": failures, "passed": not failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.path), indent=2, ensure_ascii=False))
    return 0 if not evaluate(args.path)["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
