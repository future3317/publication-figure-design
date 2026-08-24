#!/usr/bin/env python3
"""Validate the academic-figure skill's routing and evidence-first gates."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml


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
    "ReferenceDNA",
    "StyleCapsule",
    "DesignPacket",
    "DesignPatch",
    "RenderTrace",
    "pfd eval quick|full|visual|release",
    "Global visual language",
    "soft segmentation",
    "short title hierarchy",
    "whitespace is structural",
    "low-saturation semantic colors",
    "restrained legends and annotations",
    "Scientific figure-design principles",
    "figure-versus-table preflight",
    "visualize model outputs, not only metrics",
    "do not invent or exaggerate scientific effects",
    "one visual variable per experimental variable",
    "main figure answers one scientific question",
    "same sample, camera, crop, scale",
    "caption carries the explanation",
    "must run before rendering",
)


# Materials that change the behavior of a route are a contract, not optional
# background reading.  Keep this list small and route-specific; broad style
# discovery remains in the route's ordinary ``load`` list.
REQUIRED_ROUTE_LOADS: dict[str, tuple[str, ...]] = {
    "create": (
        "references/workflow-create.md",
        "references/encoding-and-uncertainty.md",
        "references/figure-family-coverage.md",
        "references/journal-specs.md",
        "references/style-spec.md",
    ),
    "concrete_reference": (
        "references/art-direction.md",
        "references/figure-family-coverage.md",
        "references/visual-grammar.md",
        "references/reference-driven-reconstruction.md",
        "references/asset-adaptation.md",
        "references/style-spec.md",
    ),
    "visual_optimization": (
        "references/art-direction.md",
        "references/visual-grammar.md",
        "references/reference-driven-reconstruction.md",
        "references/visual-reference-library.md",
        "references/checklist.md",
        "references/encoding-and-uncertainty.md",
        "references/journal-specs.md",
        "references/figure-family-coverage.md",
        "references/style-spec.md",
        "references/color-palettes.md",
    ),
    "asset_adaptation": (
        "references/asset-adaptation.md",
        "references/directory-map.md",
        "references/production-asset-metadata.md",
    ),
    "backend": ("references/backend-selection.md",),
    "qa": (
        "references/checklist.md",
        "references/delivery-contract.md",
        "references/figure-legend-contract.md",
        "references/privacy-provenance.md",
        "references/encoding-and-uncertainty.md",
        "references/export-specs.md",
    ),
    "source_reconstruction": ("references/source-reconstruction-library.md",),
    "source_review_batch": ("references/source-reconstruction-library.md",),
    "reference_intake": (
        "references/visual-reference-library.md",
        "references/figure-family-coverage.md",
        "references/privacy-provenance.md",
    ),
    "reference_benchmark": (
        "assets/reference-benchmarks/chartmimic/README.md",
        "assets/reference-benchmarks/champion_references.json",
    ),
    "eval": ("assets/reference-benchmarks/golden_tasks.json",),
    "figure_family_coverage": ("references/figure-family-coverage.md",),
    "champion_quality": (
        "references/champion-board.md",
        "assets/reference-benchmarks/champion_board.json",
        "assets/reference-benchmarks/real_generation_tasks.json",
        "assets/reference-benchmarks/visual-baseline-v1.json",
    ),
}


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
    manifest_data: dict[str, object] = {}
    if not manifest_path.is_file():
        errors.append("Missing root manifest.yaml.")
    else:
        manifest = manifest_path.read_text(encoding="utf-8", errors="replace")
        for token in ("always_load:", "routes:", "backend_policy:", "validation:"):
            if token not in manifest:
                errors.append(f"manifest.yaml is missing {token}")
        always_load = manifest.split("always_load:", 1)[-1].split("routes:", 1)[0]
        if "references/global-visual-language.md" not in always_load:
            errors.append("manifest.yaml must always load the global visual language rules.")
        try:
            parsed = yaml.safe_load(manifest)
            if isinstance(parsed, dict):
                manifest_data = parsed
            else:
                errors.append("manifest.yaml must parse to a mapping.")
        except yaml.YAMLError as exc:
            errors.append(f"manifest.yaml is not valid YAML: {exc}")

        routes = manifest_data.get("routes", {})
        if not isinstance(routes, dict):
            errors.append("manifest.yaml routes must be a mapping.")
        else:
            for route, expected in REQUIRED_ROUTE_LOADS.items():
                config = routes.get(route)
                if not isinstance(config, dict):
                    errors.append(f"manifest.yaml route '{route}' is missing.")
                    continue
                load = config.get("load", [])
                required = config.get("required_load")
                if not isinstance(load, list):
                    errors.append(f"manifest.yaml route '{route}' load must be a list.")
                    continue
                if not isinstance(required, list):
                    errors.append(f"manifest.yaml route '{route}' must declare required_load.")
                    continue
                missing = [resource for resource in expected if resource not in required]
                if missing:
                    errors.append(
                        f"manifest.yaml route '{route}' missing required_load entries: {', '.join(missing)}"
                    )
                for resource in required:
                    if not (root / resource).is_file():
                        errors.append(f"Missing required route resource: {resource}")
                outside_load = [resource for resource in required if resource not in load]
                if outside_load:
                    errors.append(
                        f"manifest.yaml route '{route}' required_load must be a subset of load: "
                        + ", ".join(outside_load)
                    )

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

    for relative in (
        "schemas/reference-dna.schema.json",
        "scripts/check_reference_dna.py",
        "scripts/evaluate_activation.py",
        "profiles/style-capsules/restrained-editorial.yaml",
        "profiles/journals/generic.yaml",
    ):
        if not (root / relative).is_file():
            errors.append(f"Missing compiler resource: {relative}")

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

    # Production scripts and figure assets use one stable entrypoint. Numbered
    # successors are a maintenance fork, while historical card metadata keeps
    # its provenance separately and is intentionally outside this scan.
    for base in (root / "scripts", root / "assets" / "figures"):
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() == ".pyc":
                continue
            if re.search(r"(?:^|[_-])(?:v\d+|final\d*|draft\d*)(?:[_-]|\.|$)", path.name, re.IGNORECASE):
                errors.append(f"Production path uses an iteration-suffixed filename: {path.relative_to(root)}")

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
