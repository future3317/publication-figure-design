#!/usr/bin/env python3
"""Materialize the mandatory evidence packet for a figure-optimization task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

try:
    from .reference_library import ReferenceLibrary
except ImportError:  # pragma: no cover - direct script execution
    from reference_library import ReferenceLibrary


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _runbook(
    before: Path, candidates: Iterable[dict[str, Any]], output_dir: Path, skill_root: Path
) -> str:
    candidate_lines = [
        f"- `{item['id']}`: `{(skill_root / item['image_path']).resolve()}` ({'; '.join(item['matches'])})"
        for item in candidates
    ]
    if not candidate_lines:
        candidate_lines = ["- No compatible reviewed candidate was returned; record `build_new` and why."]
    contract = output_dir / "visual-optimization-contract.json"
    recommendation = output_dir / "candidate-recommendation.json"
    return "\n".join((
        "# Visual-optimization runbook",
        "",
        "Do not edit plotting source until steps 1–3 are recorded in the contract.",
        "",
        "1. Open the current rendered figure:",
        f"   `{before}`",
        "2. Open every shortlisted reference image and write one pixel-level observation per candidate:",
        *candidate_lines,
        f"3. Fill `{contract}` with the selected reference, old-skeleton rejection, fresh palette decision, and intended structural changes.",
        "4. Only then edit the plotting source; make at least one structural or encoding change, not cosmetic restyling.",
        "5. Render the after figure at final physical size, build an equal-cell Before | Reference | After comparison, then run:",
        "   `python scripts/check_visual_optimization.py --contract <contract> --before <before.png> --reference <reference.png> --after <after.png> --comparison <comparison.png> --build-comparison`",
        "6. Resolve every FIX before delivery.",
        "",
        f"Shortlist evidence: `{recommendation}`",
    )) + "\n"


def prepare_packet(
    *,
    before: Path,
    figure_type: str,
    output_dir: Path,
    skill_root: Path | None = None,
    required_tags: Iterable[str] = (),
    preferred_tags: Iterable[str] = (),
    layout: str | None = None,
    data_density: str | None = None,
    n_groups: int | None = None,
    journal_style: str | None = None,
    limit: int = 3,
) -> dict[str, Path]:
    """Create the reviewable shortlist, draft contract, and exact next actions."""
    before = before.resolve()
    if not before.is_file():
        raise FileNotFoundError(f"Current rendered figure does not exist: {before}")
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    recommendation_path = output_dir / "candidate-recommendation.json"
    contract_path = output_dir / "visual-optimization-contract.json"
    runbook_path = output_dir / "RUNBOOK.md"
    existing = [path for path in (recommendation_path, contract_path, runbook_path) if path.exists()]
    if existing:
        raise FileExistsError(
            "Optimization packet already exists: " + ", ".join(str(path) for path in existing)
        )

    library = ReferenceLibrary(root=skill_root) if skill_root else ReferenceLibrary()
    recommendation = library.recommend_candidates(
        figure_type=figure_type,
        required_tags=list(required_tags),
        preferred_tags=list(preferred_tags),
        layout=layout,
        data_density=data_density,
        n_groups=n_groups,
        journal_style=journal_style,
        limit=limit,
    )
    candidate_ids = [item["id"] for item in recommendation["candidates"]]
    contract = {
        "task": "visual_optimization",
        "status": "draft",
        "before_image": str(before),
        "candidate_recommendation": recommendation,
        "reference_candidates": candidate_ids,
        "opened_reference_candidates": [],
        "candidate_pixel_observations": {},
        "selected_reference": None,
        "selection_reason": None,
        "before_diagnosis": [],
        "composition_decision": {
            "old_skeleton_removed": False,
            "hero_panel": None,
            "support_panels": None,
        },
        "palette_decision": {
            "previous_palette": [],
            "selected_palette": None,
            "semantic_mapping": {},
            "reason": None,
        },
        "structural_changes": [],
        "series_encoding_contract": {
            "method_style_map": {},
            "panel_series": {},
            "legend_scope": None,
            "same_series_style_invariant": False,
            "unresolved_orphan_series": [],
        },
        "uncertainty_contract": {
            "interval_definition": None,
            "overlap_strategy": None,
            "alpha": None,
        },
        "text_contrast": {"applicable": None},
        "visual_review": {"final_size_inspected": False},
        "final_render": {},
    }
    _write_json(recommendation_path, recommendation)
    _write_json(contract_path, contract)
    runbook_path.write_text(
        _runbook(before, recommendation["candidates"], output_dir, library.root), encoding="utf-8"
    )
    return {"recommendation": recommendation_path, "contract": contract_path, "runbook": runbook_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=Path, help="Current rendered figure.")
    parser.add_argument("--figure-type", required=True, help="Normalized figure type or supported alias.")
    parser.add_argument("--output-dir", required=True, type=Path, help="New task-local packet directory.")
    parser.add_argument("--skill-root", type=Path, help="Override the skill root (used for testing).")
    parser.add_argument("--required-tags", default="")
    parser.add_argument("--preferred-tags", default="")
    parser.add_argument("--layout")
    parser.add_argument("--data-density")
    parser.add_argument("--n-groups", type=int)
    parser.add_argument("--journal-style")
    parser.add_argument("--limit", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packet = prepare_packet(
        before=args.before,
        figure_type=args.figure_type,
        output_dir=args.output_dir,
        skill_root=args.skill_root,
        required_tags=_split(args.required_tags),
        preferred_tags=_split(args.preferred_tags),
        layout=args.layout,
        data_density=args.data_density,
        n_groups=args.n_groups,
        journal_style=args.journal_style,
        limit=args.limit,
    )
    print(json.dumps({key: str(value) for key, value in packet.items()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
