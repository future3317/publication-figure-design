#!/usr/bin/env python3
"""Validate that exact visual sources have complete manual-review evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reference_library import ReferenceLibrary


def validate_source_catalog(skill_root: Path | str, expected_count: int | None = 54) -> dict:
    skill_root = Path(skill_root)
    errors: list[str] = []
    catalog_path = skill_root / "assets/visual-references/source-reference-catalog.json"
    audit_path = skill_root / "assets/visual-references/source-reference-visual-audit.json"
    if not catalog_path.is_file():
        return {"ok": False, "errors": ["Missing source-reference catalog."], "metrics": {}}
    if not audit_path.is_file():
        return {"ok": False, "errors": ["Missing source-reference manual audit."], "metrics": {}}
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    records = catalog.get("records", [])
    decisions = audit.get("decisions", {})
    if expected_count is not None and len(records) != expected_count:
        errors.append(f"Expected {expected_count} exact visual sources; found {len(records)}.")
    blueprint_ids = {record.get("blueprint_id") for record in records}
    if set(decisions) != blueprint_ids:
        errors.append("Source-reference manual decisions do not cover each source exactly once.")
    library = ReferenceLibrary(root=skill_root, registry_path=skill_root / "assets/registry.jsonl")
    reviewed = 0
    for record in records:
        ref = library.get(record.get("reference_id", ""))
        label = record.get("blueprint_id", "unknown")
        if ref is None:
            errors.append(f"{label}: catalog reference is missing.")
            continue
        metadata = ref.metadata
        if metadata.get("reference_kind") != "exact_visual_source":
            errors.append(f"{label}: wrong reference kind.")
        if metadata.get("review_status") != "reviewed" or metadata.get("aesthetic_rating") is None:
            errors.append(f"{label}: source is not reviewed with a rating.")
        review = metadata.get("visual_review", {})
        if review.get("review_kind") != "exact-source-pixel-inspection" or not review.get("notes"):
            errors.append(f"{label}: missing direct pixel-review evidence.")
        decision = decisions.get(label, {})
        if review.get("notes") != decision.get("notes") or metadata.get("aesthetic_rating") != decision.get("rating"):
            errors.append(f"{label}: stored review differs from manual decision.")
        reviewed += metadata.get("review_status") == "reviewed"
    return {"ok": not errors, "errors": errors, "metrics": {"records": len(records), "reviewed": reviewed}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = validate_source_catalog(args.skill_root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Source reference catalog: {'PASS' if report['ok'] else 'FAIL'}")
        for error in report["errors"]:
            print(f"  ERROR: {error}")
        for key, value in report["metrics"].items():
            print(f"  {key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
