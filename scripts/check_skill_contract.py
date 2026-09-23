#!/usr/bin/env python3
"""Validate the thin skill router and manifest-owned execution contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

try:
    from check_rule_contract import validate_rules
except ImportError:  # pragma: no cover - package-style import
    from scripts.check_rule_contract import validate_rules


def _linked_paths(text: str) -> set[str]:
    return set(re.findall(r"((?:references|scripts)/[A-Za-z0-9_./-]+\.(?:md|py))", text))


def _string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _string_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _string_values(item)


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
    if len(lines) > 120:
        errors.append(f"SKILL.md has {len(lines)} lines; thin-router limit is 120.")
    frontmatter = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", skill, flags=re.DOTALL)
    if not frontmatter:
        errors.append("SKILL.md must start with YAML frontmatter.")
    else:
        if len(frontmatter.group(1)) > 1024:
            errors.append("SKILL.md frontmatter exceeds the Agent Skills 1024-character limit.")
        try:
            metadata = yaml.safe_load(frontmatter.group(1)) or {}
        except yaml.YAMLError as exc:
            metadata = {}
            errors.append(f"SKILL.md frontmatter is not valid YAML: {exc}")
        if not isinstance(metadata, dict) or metadata.get("name") != "publication-figure-design":
            errors.append("SKILL.md frontmatter name must be publication-figure-design.")
        if not isinstance(metadata, dict) or not isinstance(metadata.get("description"), str):
            errors.append("SKILL.md frontmatter must include a description.")

    if not manifest_path.is_file():
        errors.append("Missing root manifest.yaml.")
        manifest: dict = {}
        manifest_text = ""
    else:
        manifest_text = manifest_path.read_text(encoding="utf-8", errors="replace")
        try:
            manifest = yaml.safe_load(manifest_text) or {}
            if not isinstance(manifest, dict):
                errors.append("manifest.yaml must parse to a mapping.")
                manifest = {}
        except yaml.YAMLError as exc:
            errors.append(f"manifest.yaml is not valid YAML: {exc}")
            manifest = {}

    for key in ("workflows", "workflow_aliases", "rule_route_aliases", "conditions", "always_rulesets", "route_rulesets", "family_rulesets", "backend_policy", "validation"):
        if key not in manifest:
            errors.append(f"manifest.yaml is missing {key}.")
    if "always_load" in manifest or "routes" in manifest:
        errors.append("manifest.yaml must not define the legacy reading-list route contract.")
    if re.search(r"\b(required_load|always_load)\s*:", manifest_text):
        errors.append("manifest.yaml still contains a duplicated mandatory reading list.")

    try:
        from publication_figure_design.orchestrator.machine import WorkflowStage

        known_stages = {stage.value for stage in WorkflowStage}
    except ImportError as exc:
        known_stages = set()
        errors.append(f"Cannot load the runtime stage registry: {exc}")

    workflows = manifest.get("workflows", {})
    if not isinstance(workflows, dict) or not workflows:
        errors.append("manifest.yaml workflows must be a non-empty mapping.")
        workflows = {}
    for mode, config in workflows.items():
        if not isinstance(config, dict) or not isinstance(config.get("stages"), list) or not config["stages"]:
            errors.append(f"Workflow '{mode}' must declare a non-empty stages list.")
            continue
        for stage in config["stages"]:
            if stage not in known_stages:
                errors.append(f"Workflow '{mode}' references unknown stage: {stage}")
    aliases = manifest.get("workflow_aliases", {})
    if not isinstance(aliases, dict):
        errors.append("manifest.yaml workflow_aliases must be a mapping.")
        aliases = {}
    for alias, target in aliases.items():
        if target not in workflows:
            errors.append(f"Workflow alias '{alias}' targets unknown workflow: {target}")
    rule_aliases = manifest.get("rule_route_aliases", {})
    if not isinstance(rule_aliases, dict):
        errors.append("manifest.yaml rule_route_aliases must be a mapping.")
        rule_aliases = {}
    for alias, target in rule_aliases.items():
        if target not in manifest.get("route_rulesets", {}):
            errors.append(f"Rule route alias '{alias}' targets unknown ruleset route: {target}")

    conditions = manifest.get("conditions", {})
    if not isinstance(conditions, dict):
        errors.append("manifest.yaml conditions must be a mapping.")
        conditions = {}
    for name, config in conditions.items():
        if not isinstance(config, dict):
            errors.append(f"Condition '{name}' must be a mapping.")
            continue
        for stage in ([config.get("after")] if config.get("after") else []) + list(config.get("stages", [])) + list(config.get("insert_once", [])):
            if stage not in known_stages:
                errors.append(f"Condition '{name}' references unknown stage: {stage}")
        for mode in config.get("modes", []):
            if mode not in workflows:
                errors.append(f"Condition '{name}' references unknown workflow: {mode}")
            elif config.get("after") not in workflows[mode].get("stages", []):
                errors.append(f"Condition '{name}' anchor is missing from workflow '{mode}'.")
        if config.get("after") and not config.get("modes"):
            for mode, workflow in workflows.items():
                if config["after"] not in workflow.get("stages", []):
                    errors.append(f"Condition '{name}' anchor is missing from workflow '{mode}'.")

    stage_references = manifest.get("always_rulesets", [])
    if not isinstance(stage_references, list) or not stage_references:
        errors.append("manifest.yaml always_rulesets must be a non-empty list.")
        stage_references = []
    for group in (manifest.get("route_rulesets", {}), manifest.get("family_rulesets", {})):
        if not isinstance(group, dict):
            errors.append("Ruleset mappings must be mappings.")
            continue
        for key, paths in group.items():
            if not isinstance(paths, list):
                errors.append(f"Ruleset list '{key}' must be a list.")
                continue
            stage_references.extend(paths)
    for relative in dict.fromkeys(str(path) for path in stage_references):
        if not (root / relative).is_file():
            errors.append(f"Missing ruleset: {relative}")

    runtime = manifest.get("runtime", [])
    if not isinstance(runtime, list) or not runtime:
        errors.append("manifest.yaml runtime must be a non-empty bundle list.")
    else:
        for relative in runtime:
            item = str(relative).rstrip("/")
            if "*" not in item and not (root / item).exists():
                errors.append(f"Missing runtime bundle entry: {relative}")

    operations = manifest.get("operations", {})
    for command in _string_values(operations):
        script = command.split()[0]
        if script.startswith("scripts/") and not (root / script).is_file():
            errors.append(f"Missing operation script: {script}")

    for relative in sorted(_linked_paths(skill)):
        if not (root / relative).is_file():
            errors.append(f"Missing skill resource: {relative}")
    errors.extend(f"rule contract: {error}" for error in validate_rules(root)["errors"])

    for relative in ("schemas/reference-dna.schema.json", "schemas/rule.schema.json", "schemas/journal-profile.schema.json", "scripts/check_reference_dna.py", "profiles/style-capsules/restrained-editorial.yaml", "profiles/journals/generic.yaml", "agents/openai.yaml"):
        if not (root / relative).is_file():
            errors.append(f"Missing compiler resource: {relative}")

    routed_text = (skill + "\n" + manifest_text).lower()
    for phrase in ("import figures4papers", "copy figures4papers", "assets/figures4papers"):
        if phrase in routed_text:
            errors.append(f"Third-party source may be audited but must not become a runtime or copy dependency: {phrase}")

    for base in (root / "scripts", root / "assets" / "figures"):
        if base.is_dir():
            for path in base.rglob("*"):
                if path.is_file() and path.suffix.lower() != ".pyc" and re.search(r"(?:^|[_-])(?:v\d+|final\d*|draft\d*)(?:[_-]|\.|$)", path.name, re.IGNORECASE):
                    errors.append(f"Production path uses an iteration-suffixed filename: {path.relative_to(root)}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "metrics": {"skill_lines": len(lines), "workflow_count": len(workflows)},
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
