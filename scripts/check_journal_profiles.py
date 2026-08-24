#!/usr/bin/env python3
"""Check journal profile provenance metadata and report placeholders explicitly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


REQUIRED = ("source", "retrieved_at", "source_date", "status", "confidence", "review_after", "applies_to")
STATUSES = {"verified", "stale", "placeholder"}


def validate_profiles(root: Path | str) -> dict[str, object]:
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    count = 0
    placeholders = 0
    base = root / "profiles" / "journals"
    for path in sorted(base.rglob("*.yaml")):
        count += 1
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            errors.append(f"{path}: invalid YAML: {exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"{path}: profile must be a mapping")
            continue
        name = str(payload.get("name", path.stem))
        for field in REQUIRED:
            if field not in payload:
                errors.append(f"{path} ({name}): missing {field}")
        status = payload.get("status")
        if status not in STATUSES:
            errors.append(f"{path} ({name}): invalid status {status!r}")
        if status == "placeholder":
            placeholders += 1
            warnings.append(f"{path}: placeholder profile blocks technical certification")
        if status == "verified" and payload.get("verified") is not True:
            errors.append(f"{path} ({name}): verified profile must set verified: true")
        if status == "placeholder" and payload.get("verified") is True:
            errors.append(f"{path} ({name}): placeholder profile cannot set verified: true")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "metrics": {"profiles": count, "placeholders": placeholders}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_profiles(args.root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Journal profiles: {'PASS' if report['ok'] else 'FAIL'}")
        for item in report["warnings"]:
            print(f"  WARN: {item}")
        for item in report["errors"]:
            print(f"  ERROR: {item}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
