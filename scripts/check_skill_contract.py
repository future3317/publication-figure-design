#!/usr/bin/env python3
"""Validate the academic-figure skill's routing and evidence-first gates."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_PHRASES = (
    "Open every concrete reference",
    "Select implementation material",
    "exact_reuse",
    "structural_adaptation",
    "style_only",
    "build_new",
    "panel topology",
    "mark geometry",
    "layer topology",
    "data encoding",
    "annotation/legend model",
    "final assembler",
)


def _linked_paths(text: str) -> set[str]:
    return set(re.findall(r"((?:references|scripts)/[A-Za-z0-9_./-]+\.(?:md|py))", text))


def validate_skill(root: Path | str) -> dict[str, object]:
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    skill_path = root / "SKILL.md"
    manifest_path = root / "manifest.yaml"
    if not skill_path.is_file():
        return {"ok": False, "errors": ["Missing SKILL.md."], "warnings": []}
    skill = skill_path.read_text(encoding="utf-8", errors="replace")
    lines = skill.splitlines()
    if len(lines) > 300:
        errors.append(f"SKILL.md has {len(lines)} lines; router limit is 300.")
    if not re.match(r"^---\s*\nname:\s*publication-figure-design\s*\ndescription:", skill):
        errors.append("SKILL.md frontmatter must contain only the expected name and description fields.")
    manifest = ""
    if not manifest_path.is_file():
        errors.append("Missing root manifest.yaml.")
    else:
        manifest = manifest_path.read_text(encoding="utf-8", errors="replace")
        for token in ("always_load:", "routes:", "backend_policy:", "validation:"):
            if token not in manifest:
                errors.append(f"manifest.yaml is missing {token}")

    for phrase in REQUIRED_PHRASES:
        if phrase not in skill:
            errors.append(f"SKILL.md is missing required contract phrase: {phrase}")

    inspect_at = skill.find("Open every concrete reference")
    select_at = skill.find("Select implementation material")
    if inspect_at < 0 or select_at < 0 or inspect_at >= select_at:
        errors.append("Concrete-reference inspection must precede implementation-material selection.")

    routed_resources = _linked_paths(skill) | _linked_paths(manifest)
    for relative in sorted(routed_resources):
        if not (root / relative).is_file():
            errors.append(f"Missing routed resource: {relative}")

    metadata = root / "agents" / "openai.yaml"
    if not metadata.is_file():
        errors.append("Missing agents/openai.yaml.")

    routed_text = skill.lower()
    if manifest_path.is_file():
        routed_text += "\n" + manifest_path.read_text(encoding="utf-8", errors="replace").lower()
    for phrase in ("import figures4papers", "copy figures4papers", "assets/figures4papers"):
        if phrase in routed_text:
            errors.append(
                f"Third-party source may be audited but must not become a runtime or copy dependency: {phrase}"
            )

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "metrics": {"skill_lines": len(lines), "routed_resources": len(routed_resources)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_skill(args.root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Skill contract: {'PASS' if report['ok'] else 'FAIL'}")
        for error in report["errors"]:
            print(f"  ERROR: {error}")
        for warning in report["warnings"]:
            print(f"  WARN: {warning}")
        print(f"  SKILL.md lines: {report.get('metrics', {}).get('skill_lines', 'n/a')}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
