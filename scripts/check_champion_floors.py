#!/usr/bin/env python3
"""Validate champion quality-floor metadata and optional QA metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DIMENSIONS = ("typography", "whitespace", "composition", "annotations", "palette_discipline")


def check(root: Path, qa_report: Path | None = None) -> dict[str, Any]:
    champion_path = root / "assets" / "reference-benchmarks" / "champion_references.json"
    payload = json.loads(champion_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    floors = payload.get("quality_floors", {})
    for dimension in DIMENSIONS:
        value = floors.get(dimension)
        if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
            failures.append(f"missing or invalid quality floor: {dimension}")
    refs = payload.get("reference_ids", [])
    reference_floors = payload.get("reference_floors", {})
    for ref_id in refs:
        row = reference_floors.get(ref_id, {})
        for dimension in DIMENSIONS:
            if dimension not in row:
                failures.append(f"champion {ref_id} missing {dimension} floor")
    if qa_report:
        report = json.loads(qa_report.read_text(encoding="utf-8"))
        metrics = report.get("metrics", report.get("generation_summary", report))
        names = {"palette_discipline": "palette_roles"}
        for dimension in DIMENSIONS:
            key = names.get(dimension, dimension)
            if float(metrics.get(key, 0.0)) < float(floors[dimension]):
                failures.append(f"QA {key} below champion floor {floors[dimension]}")
    return {"champion_count": len(refs), "failures": failures, "passed": not failures}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-report", type=Path)
    args = parser.parse_args()
    report = check(root, args.qa_report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["failures"]:
        for failure in report["failures"]:
            print(f"CHAMPION FLOOR: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
