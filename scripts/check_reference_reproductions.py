#!/usr/bin/env python3
"""Check reproduction-code completeness for reviewed user references."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(root: Path | None = None) -> dict:
    root = root or _root()
    registry = root / "assets" / "registry.jsonl"
    findings: list[dict] = []
    checked = 0
    for line_no, line in enumerate(registry.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("reference_kind") != "user_supplied":
            continue
        if record.get("review_status") not in {"reviewed", "promoted"}:
            continue
        checked += 1
        for field in ("code_path", "reproduction_preview_path"):
            value = record.get(field)
            if not value:
                findings.append({"line": line_no, "id": record.get("id"), "field": field, "detail": "missing metadata path"})
                continue
            if not (root / value).is_file():
                findings.append({"line": line_no, "id": record.get("id"), "field": field, "detail": f"file not found: {value}"})
    return {"checked": checked, "failures": len(findings), "findings": findings, "healthy": not findings}


if __name__ == "__main__":
    report = run()
    print(f"Reviewed user references checked: {report['checked']}")
    if report["findings"]:
        for item in report["findings"]:
            print(f"FAIL {item['id']} {item['field']}: {item['detail']}")
        sys.exit(1)
    print("Reference reproductions: PASS")
