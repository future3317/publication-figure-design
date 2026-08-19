#!/usr/bin/env python3
"""Validate visual-audit evidence for user-supplied reference reconstructions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from .visual_evidence import comparison_contains, load_image
except ImportError:
    from visual_evidence import comparison_contains, load_image


FEATURES = ("topology", "marks_layers", "data_encoding", "hierarchy_spacing", "palette_roles", "annotations")


def run(root: Path | None = None) -> dict:
    root = root or Path(__file__).resolve().parents[1]
    audit_path = root / "assets" / "visual-references" / "review-evidence" / "reproduction-audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for record in audit.get("records", []):
        ref_id = record.get("id")
        base = root / "assets" / "visual-references"
        metadata_path = base / "references" / ref_id / "metadata.json"
        reference = base / "references" / ref_id / "image.png"
        if metadata_path.is_file():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            image_path = metadata.get("image_path")
            if image_path:
                reference = root / image_path
        candidate = base / "references" / ref_id / "reconstruction.png"
        comparison = base / "review-evidence" / "reproduction-audit" / f"{ref_id}-reference-vs-reconstruction.png"
        for path in (reference, candidate, comparison):
            if not path.is_file():
                failures.append(f"{ref_id}: missing {path.relative_to(root)}")
        if reference.is_file() and candidate.is_file() and comparison.is_file():
            try:
                if not comparison_contains(comparison, [reference, candidate]):
                    failures.append(f"{ref_id}: comparison is not an authentic equal-cell pair")
            except ValueError as exc:
                failures.append(f"{ref_id}: invalid image evidence ({exc})")
        if record.get("overall") not in {"pass", "justified_deviation"}:
            failures.append(f"{ref_id}: invalid overall review status")
        if not record.get("deviations"):
            failures.append(f"{ref_id}: deviations/review rationale is missing")
        feature_map = record.get("features", {})
        for feature in FEATURES:
            if feature_map.get(feature) not in {"pass", "justified_deviation"}:
                failures.append(f"{ref_id}: unresolved feature {feature}")
    expected = 14
    if len(audit.get("records", [])) != expected:
        failures.append(f"expected {expected} audited user references, found {len(audit.get('records', []))}")
    return {"checked": len(audit.get("records", [])), "failures": failures, "healthy": not failures}


if __name__ == "__main__":
    report = run()
    print(f"Reference reconstruction fidelity audits checked: {report['checked']}")
    if report["failures"]:
        for failure in report["failures"]:
            print(f"FAIL {failure}")
        sys.exit(1)
    print("Reference reconstruction fidelity: PASS (all deviations explicitly recorded)")
