#!/usr/bin/env python3
"""Validate machine-readable PFD rules and their source provenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


SCOPES = {"global", "house", "journal", "family", "backend", "eval"}
SEVERITIES = {"block", "warn", "advisory"}
MODES = {"automated", "manual", "hybrid"}
AUTHORITIES = {"normative", "publisher_requirement", "scientific_integrity", "evidence_based_guidance", "house_style", "heuristic"}


def _load_yaml(path: Path, errors: list[str]) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML: {exc}")
        return None


def _rule_items(path: Path, payload: Any, errors: list[str]) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "rules" in payload:
        payload = payload["rules"]
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        errors.append(f"{path}: expected a rule mapping or rules list")
        return []
    items: list[dict[str, Any]] = []
    for index, rule in enumerate(payload):
        if not isinstance(rule, dict):
            errors.append(f"{path} rule {index}: expected mapping")
            continue
        items.append(rule)
    return items


def validate_rules(root: Path | str) -> dict[str, object]:
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    rules_root = root / "rules"
    registry_path = root / "sources" / "registry.yaml"
    if not rules_root.is_dir():
        return {"ok": False, "errors": ["Missing rules/ directory."], "warnings": []}
    if not registry_path.is_file():
        return {"ok": False, "errors": ["Missing sources/registry.yaml."], "warnings": []}

    registry = _load_yaml(registry_path, errors)
    source_rows = registry.get("sources", []) if isinstance(registry, dict) else []
    if not isinstance(source_rows, list):
        errors.append("sources/registry.yaml: sources must be a list")
        source_rows = []
    sources: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        if not isinstance(row, dict) or not row.get("id"):
            errors.append("sources/registry.yaml: every source needs an id")
            continue
        source_id = str(row["id"])
        if source_id in sources:
            errors.append(f"sources/registry.yaml: duplicate source id {source_id}")
        sources[source_id] = row
        for field in ("publisher", "title", "url", "authority", "retrieved_at", "status", "confidence", "review_after"):
            if not row.get(field):
                errors.append(f"sources/registry.yaml source {source_id}: missing {field}")

    ids: set[str] = set()
    conflict_refs: list[tuple[str, str]] = []
    rule_count = 0
    for path in sorted(rules_root.rglob("*.yaml")):
        if path.name == "_index.yaml":
            continue
        payload = _load_yaml(path, errors)
        for rule in _rule_items(path, payload, errors):
            rule_count += 1
            rule_id = str(rule.get("id", ""))
            if not rule_id:
                errors.append(f"{path}: rule missing id")
            elif rule_id in ids:
                errors.append(f"{path}: duplicate rule id {rule_id}")
            else:
                ids.add(rule_id)
            conflicts = rule.get("conflicts_with", [])
            if conflicts is not None and not isinstance(conflicts, list):
                errors.append(f"{path} {rule_id}: conflicts_with must be a list")
            elif isinstance(conflicts, list):
                conflict_refs.extend((rule_id, str(item)) for item in conflicts)
            if not rule.get("title"):
                errors.append(f"{path} {rule_id}: missing title")
            if rule.get("scope") not in SCOPES:
                errors.append(f"{path} {rule_id}: invalid scope {rule.get('scope')!r}")
            if rule.get("severity") not in SEVERITIES:
                errors.append(f"{path} {rule_id}: invalid severity {rule.get('severity')!r}")
            authority = rule.get("authority")
            if authority is not None and authority not in AUTHORITIES:
                errors.append(f"{path} {rule_id}: invalid authority {authority!r}")
            if not isinstance(rule.get("statement"), str) or not rule["statement"].strip():
                errors.append(f"{path} {rule_id}: missing statement")
            verification = rule.get("verification")
            if not isinstance(verification, dict):
                errors.append(f"{path} {rule_id}: missing verification mapping")
            else:
                if verification.get("mode") not in MODES:
                    errors.append(f"{path} {rule_id}: invalid verification mode")
                if not isinstance(verification.get("checks"), list) or not verification["checks"]:
                    errors.append(f"{path} {rule_id}: verification.checks must be non-empty")
            evidence = rule.get("evidence", [])
            if not isinstance(evidence, list):
                errors.append(f"{path} {rule_id}: evidence must be a list")
                evidence = []
            if rule.get("severity") == "block" and not evidence:
                errors.append(f"{path} {rule_id}: block rule requires source evidence")
            for item in evidence:
                if not isinstance(item, dict) or not item.get("source_id"):
                    errors.append(f"{path} {rule_id}: every evidence item needs source_id")
                elif item["source_id"] not in sources:
                    errors.append(f"{path} {rule_id}: unknown source {item['source_id']}")
            override = rule.get("override", {})
            if rule.get("severity") == "block" and isinstance(override, dict) and override.get("allowed"):
                errors.append(f"{path} {rule_id}: block rule cannot allow override")

    for source_id, target_id in conflict_refs:
        if target_id not in ids:
            errors.append(f"rule {source_id}: conflicts_with references unknown rule {target_id}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "metrics": {"rule_count": rule_count, "source_count": len(sources)},
        "rule_ids": sorted(ids),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_rules(args.root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Rule contract: {'PASS' if report['ok'] else 'FAIL'}")
        for error in report["errors"]:
            print(f"  ERROR: {error}")
        print(f"  Rules: {report.get('metrics', {}).get('rule_count', 0)}")
        print(f"  Sources: {report.get('metrics', {}).get('source_count', 0)}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
