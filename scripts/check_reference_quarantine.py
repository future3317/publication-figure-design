#!/usr/bin/env python3
"""Check the raw → analyzed → reviewed → benchmarked → production lifecycle."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


STATES = {"raw", "analyzed", "reviewed", "benchmarked", "production", "rejected"}


def check(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    records = []
    failures: list[str] = []
    legacy = 0
    for path in sorted((root / "assets" / "visual-references").glob("**/metadata.json")):
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            failures.append(f"{path}: invalid metadata ({exc})")
            continue
        state = metadata.get("lifecycle_state")
        if state is None:
            legacy += 1
            continue
        if state not in STATES:
            failures.append(f"{metadata.get('id')}: invalid lifecycle_state={state!r}")
            continue
        quarantine = metadata.get("quarantine")
        if not isinstance(quarantine, dict) or quarantine.get("state") != state:
            failures.append(f"{metadata.get('id')}: quarantine state does not match lifecycle_state")
        if state == "production":
            history = quarantine.get("history", []) if isinstance(quarantine, dict) else []
            if not any(isinstance(item, dict) and item.get("state") == "production" for item in history):
                failures.append(f"{metadata.get('id')}: production reference lacks promotion evidence")
            if metadata.get("production_ready") is not True:
                failures.append(f"{metadata.get('id')}: production state requires production_ready=true")
        records.append({"id": metadata.get("id"), "state": state})
    return {"checked": len(records), "legacy_missing_state": legacy, "failures": failures, "passed": not failures}


if __name__ == "__main__":
    report = check()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["failures"]:
        for failure in report["failures"]:
            print(f"REFERENCE QUARANTINE: {failure}", file=sys.stderr)
        raise SystemExit(1)
