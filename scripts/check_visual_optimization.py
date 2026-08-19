#!/usr/bin/env python3
"""Validate rendered evidence for a visual-optimization task."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from .visual_evidence import comparison_contains, compose_equal_size_comparison, load_image
    from .rendered_contrast import inspect_text_contrast
    from .visual_grammar import validate_visual_grammar
    from .compare_output_to_reference import compare_output_to_reference
except ImportError:  # pragma: no cover - direct CLI execution
    from visual_evidence import comparison_contains, compose_equal_size_comparison, load_image
    from rendered_contrast import inspect_text_contrast
    from visual_grammar import validate_visual_grammar
    from compare_output_to_reference import compare_output_to_reference
from PIL import ImageChops, ImageStat


STRUCTURAL_TERMS = {
    "axis", "direct-label", "facet", "geometry", "grid", "gridspec", "layer",
    "layout", "legend", "mark", "panel", "ratio", "subplot", "topology",
    "坐标", "几何", "图层", "布局", "面板", "图例", "层级",
}
COSMETIC_TERMS = {"alpha", "color", "colour", "font", "linewidth", "palette", "spacing", "颜色", "字体", "线宽"}
STRUCTURAL_ACTIONS = {
    "add", "direct-label", "merge", "move", "remove", "reorder", "replace", "resize",
    "restructure", "split", "添加", "合并", "移动", "删除", "重排", "替换", "重构", "拆分",
}
REVIEW_FIELDS = {
    "hierarchy", "panel_balance", "whitespace", "legend_footprint", "text_legibility",
    "cross_panel_semantics", "legend_data_separation", "uncertainty_legibility",
    "axis_label_compactness",
}
ART_DIRECTION_IDS = {
    "hero_illustration",
    "editorial_evidence_chain",
    "modular_blueprint",
    "specimen_evidence_atlas",
    "analytic_minimalism",
    "comparative_storyboard",
}


def _nonempty(value: Any) -> bool:
    return bool(value.strip()) if isinstance(value, str) else bool(value)


def _has_structural_changes(changes: Any) -> bool:
    if not isinstance(changes, list) or not changes:
        return False
    text = " ".join(str(change).lower() for change in changes)
    return any(term in text for term in STRUCTURAL_TERMS) and any(
        action in text for action in STRUCTURAL_ACTIONS
    )


def _visibly_different(first_path: Path | str, second_path: Path | str) -> bool:
    first = load_image(first_path)
    second = load_image(second_path).resize(first.size)
    mean_difference = sum(ImageStat.Stat(ImageChops.difference(first, second)).mean) / 3
    return mean_difference >= 0.5


def _validate_final_render(contract: dict[str, Any], after_path: Path | str) -> tuple[bool, str]:
    """Check that the delivered raster is plausibly rendered at its declared size."""
    spec = contract.get("final_render")
    if not isinstance(spec, dict):
        return False, "Declare final physical render width_mm, height_mm, dpi, and tolerance_mm."
    try:
        width_mm = float(spec["width_mm"])
        height_mm = float(spec["height_mm"])
        dpi = float(spec["dpi"])
        tolerance_mm = float(spec.get("tolerance_mm", 3.0))
    except (KeyError, TypeError, ValueError):
        return False, "Final physical render declaration is incomplete or non-numeric."
    if min(width_mm, height_mm, dpi) <= 0 or tolerance_mm < 0:
        return False, "Final physical render dimensions and DPI must be positive."
    try:
        image = load_image(after_path)
    except ValueError as exc:
        return False, str(exc)
    actual_width_mm = image.width / dpi * 25.4
    actual_height_mm = image.height / dpi * 25.4
    if abs(actual_width_mm - width_mm) > tolerance_mm or abs(actual_height_mm - height_mm) > tolerance_mm:
        return False, (
            f"After raster is {actual_width_mm:.1f}x{actual_height_mm:.1f} mm at {dpi:g} dpi, "
            f"outside declared {width_mm:g}x{height_mm:g} mm ±{tolerance_mm:g} mm."
        )
    return True, ""


def validate_visual_optimization(
    contract: dict[str, Any],
    before_path: Path | str,
    after_path: Path | str,
    reference_path: Path | str,
    comparison_path: Path | str,
) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    candidates = contract.get("reference_candidates") or []
    opened = contract.get("opened_reference_candidates") or []
    selected = contract.get("selected_reference")
    recommendation = contract.get("candidate_recommendation")
    recommendation_candidates = (
        recommendation.get("candidates", []) if isinstance(recommendation, dict) else []
    )
    recommended_ids = [item.get("id") for item in recommendation_candidates if isinstance(item, dict)]
    checks["recommendation_report"] = bool(recommendation_candidates)
    if not checks["recommendation_report"]:
        errors.append("A candidate recommendation report with at least one compatible candidate is required.")
    checks["candidate_ids_match_report"] = candidates == recommended_ids
    if not checks["candidate_ids_match_report"]:
        errors.append("Reference candidate IDs must exactly match the recommendation report order.")
    checks["reference_selected"] = 1 <= len(candidates) <= 3 and selected in candidates
    if not checks["reference_selected"]:
        errors.append("Select one reference from one to three compatible candidates.")
    checks["reference_opened"] = bool(selected) and selected in opened
    if not checks["reference_opened"]:
        errors.append("The selected reference must be opened and its pixels inspected.")
    checks["all_candidates_opened"] = set(candidates) == set(opened)
    if not checks["all_candidates_opened"]:
        errors.append("Every recommended candidate must be opened before selection.")
    observations = contract.get("candidate_pixel_observations")
    observations = observations if isinstance(observations, dict) else {}
    missing_observations = [candidate for candidate in candidates if not str(observations.get(candidate, "")).strip()]
    checks["candidate_pixel_observations"] = not missing_observations
    if missing_observations:
        errors.append("Missing pixel observation for candidate(s): " + ", ".join(missing_observations))
    grammar_errors = validate_visual_grammar(contract.get("selected_reference_visual_grammar"))
    checks["selected_reference_visual_grammar"] = not grammar_errors
    errors.extend(grammar_errors)
    checks["selection_reason"] = bool(str(contract.get("selection_reason", "")).strip())
    if not checks["selection_reason"]:
        errors.append("Record why the selected reference is the best structural visual match.")
    palette = contract.get("palette_decision")
    palette = palette if isinstance(palette, dict) else {}
    palette_fields = ("previous_palette", "selected_palette", "semantic_mapping", "reason")
    missing_palette_fields = [field for field in palette_fields if not _nonempty(palette.get(field))]
    checks["palette_reconsidered"] = not missing_palette_fields
    if missing_palette_fields:
        errors.append(
            "Record an explicit palette decision for this optimization (prior colors, selected library palette or retained colors, semantic mapping, and reason)."
        )
    art_direction = contract.get("art_direction")
    art_direction = art_direction if isinstance(art_direction, dict) else {}
    checks["art_direction"] = (
        art_direction.get("id") in ART_DIRECTION_IDS
        and bool(str(art_direction.get("reason", "")).strip())
    )
    if not checks["art_direction"]:
        errors.append(
            "Select one declared art direction and explain how it serves the evidence; 'unselected' is not a delivery state."
        )
    # A polished multi-panel figure must keep the same method identity across
    # panels.  This catches the common failure where a global legend says one
    # thing, a local legend silently renames it, or a new color/marker appears
    # in a panel without a declared role.
    series_contract = contract.get("series_encoding_contract")
    series_contract = series_contract if isinstance(series_contract, dict) else {}
    method_style_map = series_contract.get("method_style_map")
    panel_series = series_contract.get("panel_series")
    legend_scope = series_contract.get("legend_scope")
    unresolved_orphans = series_contract.get("unresolved_orphan_series")
    checks["cross_panel_semantics"] = (
        isinstance(method_style_map, dict) and bool(method_style_map)
        and isinstance(panel_series, dict) and bool(panel_series)
        and legend_scope in {"global", "panel_local", "direct_labels", "mixed_declared"}
        and series_contract.get("same_series_style_invariant") is True
        and isinstance(unresolved_orphans, list) and not unresolved_orphans
    )
    if not checks["cross_panel_semantics"]:
        errors.append(
            "Declare a cross-panel series encoding contract: stable method color/linestyle/marker, per-panel series membership, legend scope, and no unresolved orphan series."
        )
    uncertainty_contract = contract.get("uncertainty_contract")
    uncertainty_contract = uncertainty_contract if isinstance(uncertainty_contract, dict) else {}
    interval_definition = uncertainty_contract.get("interval_definition")
    overlap_strategy = uncertainty_contract.get("overlap_strategy")
    alpha = uncertainty_contract.get("alpha")
    alpha_ok = alpha is None or (isinstance(alpha, (int, float)) and 0 < float(alpha) <= 0.35)
    checks["uncertainty_contract"] = (
        isinstance(interval_definition, str) and bool(interval_definition.strip())
        and isinstance(overlap_strategy, str) and bool(overlap_strategy.strip())
        and alpha_ok
    )
    if not checks["uncertainty_contract"]:
        errors.append(
            "Declare uncertainty interval meaning, overlap/occlusion strategy, and ribbon alpha (or explicitly mark uncertainty as not applicable)."
        )
    text_contrast = contract.get("text_contrast")
    text_contrast = text_contrast if isinstance(text_contrast, dict) else {}
    if text_contrast.get("applicable") is True:
        contrast_report = text_contrast.get("report")
        contrast_report = contrast_report if isinstance(contrast_report, dict) else {}
        regions = contrast_report.get("regions")
        regions = regions if isinstance(regions, list) else []
        declared_ok = (
            contrast_report.get("ready") is True
            and contrast_report.get("minimum_ratio", 0) >= 4.5
            and isinstance(regions, list)
            and bool(regions)
            and all(region.get("pass") is True and region.get("contrast_ratio", 0) >= 4.5 for region in regions if isinstance(region, dict))
        )
        region_boxes = [
            tuple(region["region"])
            for region in regions
            if isinstance(region, dict)
            and isinstance(region.get("region"), list)
            and len(region["region"]) == 4
        ]
        actual = inspect_text_contrast(
            after_path, region_boxes, float(contrast_report.get("minimum_ratio", 4.5))
        ) if declared_ok and region_boxes else {"ready": False, "regions": []}
        checks["rendered_text_contrast"] = declared_ok and actual.get("ready") is True
        if not checks["rendered_text_contrast"]:
            errors.append("Text on a colored fill requires a passing contrast report recomputed from the supplied after raster; stale or self-authored ratios do not pass.")
    else:
        checks["rendered_text_contrast"] = text_contrast.get("applicable") is False
        if not checks["rendered_text_contrast"]:
            errors.append("Declare whether the optimized figure contains text on colored fills; do not omit contrast applicability.")
    diagnosis = contract.get("before_diagnosis")
    checks["before_diagnosed"] = isinstance(diagnosis, list) and bool(diagnosis)
    if not checks["before_diagnosed"]:
        errors.append("Record a structural and hierarchical diagnosis of the before render.")
    changes = contract.get("structural_changes")
    checks["structural_change"] = _has_structural_changes(changes)
    if not checks["structural_change"]:
        errors.append("Cosmetic-only color/font/alpha/linewidth/spacing edits do not qualify as visual optimization; record structural changes.")
    # A structural-change sentence is not enough when the rendered figure
    # still follows the old equal-weight subplot skeleton.  The author must
    # state what was removed and how hierarchy is rebuilt; this is the failure
    # mode that previously let cosmetic re-tuning pass as a redesign.
    composition = contract.get("composition_decision")
    composition = composition if isinstance(composition, dict) else {}
    checks["old_skeleton_rejected"] = (
        composition.get("old_skeleton_removed") is True
        and bool(str(composition.get("hero_panel", "")).strip())
        and bool(str(composition.get("support_panels", "")).strip())
    )
    if not checks["old_skeleton_rejected"]:
        errors.append("State how the old figure skeleton was removed and how hero/support panel hierarchy is rebuilt; otherwise the redesign may still be a cosmetic retune of the old grid.")
    review = contract.get("visual_review") if isinstance(contract.get("visual_review"), dict) else {}
    checks["final_size_inspected"] = review.get("final_size_inspected") is True
    if not checks["final_size_inspected"]:
        errors.append("The after render must be inspected at final physical size.")
    missing_reviews = sorted(field for field in REVIEW_FIELDS if review.get(field) not in {"pass", "justified_deviation"})
    checks["visual_review_complete"] = not missing_reviews
    if missing_reviews:
        errors.append("Missing rendered visual review fields: " + ", ".join(missing_reviews))
    checks["final_render_dimensions"], render_error = _validate_final_render(contract, after_path)
    if not checks["final_render_dimensions"]:
        errors.append(render_error)
    for label, path in (("before", before_path), ("after", after_path), ("reference", reference_path), ("comparison", comparison_path)):
        try:
            load_image(path)
            checks[f"{label}_image"] = True
        except ValueError as exc:
            checks[f"{label}_image"] = False
            errors.append(str(exc))
    selected_record = next(
        (item for item in recommendation_candidates if item.get("id") == selected), None
    )
    expected_hash = selected_record.get("image_sha256") if selected_record else None
    actual_hash = (
        hashlib.sha256(Path(reference_path).read_bytes()).hexdigest()
        if checks.get("reference_image") else None
    )
    checks["selected_reference_hash"] = bool(expected_hash) and expected_hash == actual_hash
    if not checks["selected_reference_hash"]:
        errors.append("Selected reference pixels do not match the recommendation report SHA-256.")
    if all(checks.get(f"{label}_image") for label in ("before", "after", "reference", "comparison")):
        checks["before_after_differ"] = _visibly_different(before_path, after_path)
        if not checks["before_after_differ"]:
            errors.append("Before and after renders do not visibly differ.")
        checks["comparison_authentic"] = comparison_contains(
            comparison_path, [before_path, reference_path, after_path]
        )
        if not checks["comparison_authentic"]:
            errors.append("Comparison image does not contain the supplied before, reference, and after renders in equal-size cells.")
        # Process evidence (opened candidates, declarations, and a Before|Reference|After
        # strip) is not a fidelity measurement. Recompute alignment from the final after
        # raster so a stale contract cannot pass a visually mismatched redesign.
        alignment = compare_output_to_reference(reference_path, after_path)
        checks["reference_alignment_gate"] = alignment.get("verdict") == "pass"
        checks["reference_alignment_metrics"] = alignment.get("metrics", {})
        if not checks["reference_alignment_gate"]:
            errors.append(
                "Final after raster fails the reference-alignment gate: "
                f"overall_style_similarity={alignment.get('metrics', {}).get('overall_style_similarity', 0):.3f}."
            )
    return {"ready": not errors, "status": "READY" if not errors else "FIX", "errors": errors, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--build-comparison", action="store_true")
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()
    if args.build_comparison:
        compose_equal_size_comparison([args.before, args.reference, args.after], args.comparison)
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    report = validate_visual_optimization(contract, args.before, args.after, args.reference, args.comparison)
    print(f"Visual Optimization: {report['status']}")
    for error in report["errors"]:
        print(f"  ERROR: {error}")
    if args.json_path:
        args.json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
