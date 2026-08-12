#!/usr/bin/env python3
"""Validate process evidence for reference-driven figure reconstruction."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "reference_source",
    "scientific_invariants",
    "canvas_layout",
    "mark_geometry",
    "layer_topology",
    "data_encoding",
    "palette_roles",
    "typography",
    "legend_annotation",
    "spacing_hierarchy",
    "must_match",
    "may_adapt",
    "implementation_decision",
    "adaptation_level",
    "decision_evidence",
    "structural_changes",
    "fidelity_review",
)

DECISIONS = {"reuse", "restructure", "rewrite"}
ADAPTATION_LEVELS = {"exact_reuse", "structural_adaptation", "style_only", "build_new"}
ALLOWED_ADAPTATIONS = {
    "reuse": {"exact_reuse"},
    "restructure": {"structural_adaptation"},
    "rewrite": {"style_only", "build_new"},
}


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _has_structural_evidence(changes: Any) -> bool:
    if not isinstance(changes, list) or not changes:
        return False
    structural_terms = {
        "axis", "facet", "geometry", "grid", "gridspec", "layer", "layout", "legend model",
        "mark", "marginal", "panel", "subplot", "topology", "坐标", "几何", "图层", "布局", "面板",
    }
    text = " ".join(str(item).lower() for item in changes)
    return any(term in text for term in structural_terms)


def validate_reference_fidelity(
    script_text: str,
    contract: dict[str, Any],
    comparison_path: Path | str | None = None,
) -> dict[str, Any]:
    """Return a READY/FIX report without comparing data-dependent pixels."""
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}

    checks["reference_marker"] = bool(
        re.search(r"^#\s*AFS-REFERENCE-DRIVEN:\s*true\s*$", script_text, re.MULTILINE | re.IGNORECASE)
    )
    if not checks["reference_marker"]:
        errors.append("Missing '# AFS-REFERENCE-DRIVEN: true' script marker.")

    missing = [field for field in REQUIRED_FIELDS if not _nonempty(contract.get(field))]
    checks["contract_complete"] = not missing
    if missing:
        errors.append("Missing or empty contract fields: " + ", ".join(missing))

    decision = str(contract.get("implementation_decision", "")).strip().lower()
    checks["decision_valid"] = decision in DECISIONS
    if not checks["decision_valid"]:
        errors.append("implementation_decision must be reuse, restructure, or rewrite.")

    adaptation_level = str(contract.get("adaptation_level", "")).strip().lower()
    checks["adaptation_level_valid"] = adaptation_level in ADAPTATION_LEVELS
    if not checks["adaptation_level_valid"]:
        errors.append(
            "adaptation_level must be exact_reuse, structural_adaptation, style_only, or build_new."
        )
    elif checks["decision_valid"] and adaptation_level not in ALLOWED_ADAPTATIONS[decision]:
        errors.append(
            f"Reference decision '{decision}' is incompatible with adaptation_level "
            f"'{adaptation_level}'."
        )

    marker = re.search(
        r"^#\s*AFS-ADAPTATION-LEVEL:\s*(\S+)\s*$", script_text, re.MULTILINE | re.IGNORECASE
    )
    checks["adaptation_marker"] = bool(marker) and marker.group(1).lower() == adaptation_level
    if not checks["adaptation_marker"]:
        errors.append("Missing or inconsistent AFS-ADAPTATION-LEVEL script marker.")

    if decision == "reuse":
        evidence = contract.get("structural_compatibility")
        checks["reuse_compatibility"] = isinstance(evidence, list) and len(evidence) >= 5
        if not checks["reuse_compatibility"]:
            errors.append(
                "Reuse requires structural compatibility evidence for panel topology, mark geometry, "
                "layer topology, data encoding, and annotation/legend model."
            )
    elif decision in {"restructure", "rewrite"}:
        changes = contract.get("structural_changes")
        checks["structural_change"] = _has_structural_evidence(changes)
        if not checks["structural_change"]:
            errors.append(
                f"{decision} requires explicit structural changes to layout/panels/geometry/layers/encodings; "
                "vague or cosmetic-only color/font/alpha/linewidth edits do not qualify."
            )

    must_match = contract.get("must_match") if isinstance(contract.get("must_match"), list) else []
    reviews = contract.get("fidelity_review") if isinstance(contract.get("fidelity_review"), list) else []
    review_by_feature = {
        str(item.get("feature")): item for item in reviews if isinstance(item, dict) and item.get("feature")
    }
    unresolved: list[str] = []
    bad_deviations: list[str] = []
    for feature in must_match:
        item = review_by_feature.get(str(feature))
        status = str(item.get("status", "")).lower() if item else ""
        if status not in {"pass", "justified_deviation"}:
            unresolved.append(str(feature))
        elif status == "justified_deviation" and not _nonempty(item.get("reason")):
            bad_deviations.append(str(feature))

    checks["must_match_resolved"] = not unresolved
    if unresolved:
        errors.append("Unresolved must-match features: " + ", ".join(unresolved))
    checks["deviations_justified"] = not bad_deviations
    if bad_deviations:
        errors.append("Justified deviations require a reason: " + ", ".join(bad_deviations))

    if comparison_path is not None:
        path = Path(comparison_path)
        checks["comparison_exists"] = path.is_file() and path.stat().st_size > 0
        if not checks["comparison_exists"]:
            errors.append(f"Comparison image is missing or empty: {path}")
    else:
        checks["comparison_exists"] = False
        warnings.append("No comparison image supplied; rendered delivery is not yet verifiable.")

    return {
        "ready": not errors,
        "status": "READY" if not errors else "FIX",
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--comparison", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()

    script_text = args.script.read_text(encoding="utf-8")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    report = validate_reference_fidelity(script_text, contract, args.comparison)

    print(f"Reference Fidelity: {report['status']}")
    for error in report["errors"]:
        print(f"  ERROR: {error}")
    for warning in report["warnings"]:
        print(f"  WARN: {warning}")
    if args.json_path:
        args.json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
