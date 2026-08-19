"""Taxonomy and reference-library coverage audit for scientific figure families."""

from __future__ import annotations

import argparse
import json
from typing import Any


FIGURE_FAMILIES: dict[str, dict[str, Any]] = {
    "comparison_effect": {
        "figure_types": ["grouped_bar", "bar_comparison", "grouped_violin", "boxplot", "raincloud", "forest_interval", "bland_altman"],
        "selection_rule": "Use categorical marks for independent groups; use dots/lines or an interval plot for paired effects and preserve the replicate distribution.",
        "must_observe": ["group spacing and baseline", "raw-point/interval treatment", "comparison direction and zero reference"],
    },
    "distribution_uncertainty": {
        "figure_types": ["distribution_grid", "histogram_overlay", "density", "ridge", "ecdf", "survival"],
        "selection_rule": "Show the observed distribution before summarizing it; choose ECDF or survival curves when rank/time-to-event information is the claim.",
        "must_observe": ["bin or bandwidth logic", "sample points and n", "interval/quantile definition", "shared or independent scales"],
    },
    "trend_trajectory": {
        "figure_types": ["line_trend", "line_grid", "learning_curves", "time_series", "event_timeline", "trajectory"],
        "selection_rule": "Use lines only when x has an ordered or continuous meaning; distinguish repeated measurements, trajectories, and event times.",
        "must_observe": ["x ordering and sampling cadence", "line identity across panels", "ribbon meaning", "missingness and endpoint treatment"],
    },
    "paired_operating_point": {
        "figure_types": ["paired_comparison", "operating_point", "dumbbell", "slopegraph", "small_multiple_comparison"],
        "selection_rule": "Use connected pairs or aligned small multiples for matched observations; do not imply a continuous trend between method-specific operating states.",
        "must_observe": ["pair identity", "connection direction", "reference/target ordering", "uncertainty and overlap"],
    },
    "classification_diagnostics": {
        "figure_types": ["roc", "pr_curve", "calibration", "confusion_matrix", "lift_gain", "decision_curve"],
        "selection_rule": "Separate ranking (ROC/PR) from probability quality (calibration) and threshold decisions; report prevalence and the operating point.",
        "must_observe": ["class prevalence", "threshold markers", "diagonal/baseline meaning", "bin counts or confidence bands"],
    },
    "relationship_embedding": {
        "figure_types": ["scatter_bubble", "scatter_marginal", "scatter_regression", "pca", "umap", "tsne", "manifold_3d", "correlation"],
        "selection_rule": "Use scatter geometry for relationships and embedding maps for geometry in a learned space; do not turn an embedding into a causal or quantitative axis claim.",
        "must_observe": ["axis units or embedding disclaimer", "point/label density", "regression and uncertainty", "occlusion and outlier policy"],
    },
    "matrix_array": {
        "figure_types": ["heatmap", "heatmap_grid", "correlation_matrix", "confusion_matrix", "clustermap", "network_matrix"],
        "selection_rule": "Declare the matrix normalization and color midpoint; use clustering only when the ordering is evidence rather than decoration.",
        "must_observe": ["row/column order", "color scale and midpoint", "cell text contrast", "missing/zero encoding", "dendrogram or separators"],
    },
    "network_flow_set": {
        "figure_types": ["network", "network_matrix", "sankey", "alluvial", "chord", "upset", "venn", "pathway"],
        "selection_rule": "Use nodes/edges for relational structure, flow widths for conserved quantities, and UpSet for many-set membership; never use line crossings as an unencoded channel.",
        "must_observe": ["node/edge roles", "direction and arrowheads", "weight scale", "layout stability", "label collision strategy"],
    },
    "spatial_image": {
        "figure_types": ["spatial_image_plate", "microscopy", "segmentation_overlay", "map", "spatial_field", "single_cell_systems", "in_vivo_efficacy"],
        "selection_rule": "Pair image evidence with quantitative readouts; preserve scale, orientation, acquisition context, and any segmentation/registration uncertainty.",
        "must_observe": ["scale bar and orientation", "crop/field-of-view", "overlay semantics", "intensity normalization", "quantification linkage"],
    },
    "mechanism_architecture": {
        "figure_types": ["mechanism_schematic", "architecture_schematic", "conceptual_multi_panel", "material_mechanism", "workflow", "pipeline", "causal_diagram"],
        "selection_rule": "Use a schematic to explain entities and transformations, then support the mechanism with data panels; distinguish semantic arrows from measured vectors.",
        "must_observe": ["object geometry/material", "arrow path and direction", "stage grouping", "occlusion/layer order", "legend or direct-label scope"],
    },
    "statistical_discovery": {
        "figure_types": ["volcano", "ma", "manhattan", "enrichment", "forest", "forest_interval", "funnel", "effect_size"],
        "selection_rule": "Make the statistical threshold and multiplicity context visible; highlight discoveries without hiding the full tested population.",
        "must_observe": ["threshold lines", "significance/effect axes", "label selection", "multiple-testing or interval meaning"],
    },
    "optimization_sensitivity": {
        "figure_types": ["ablation", "bar_ablation", "sensitivity", "perturbation", "robustness", "pareto", "scaling_analysis", "benchmark"],
        "selection_rule": "Use one controlled change per ablation and reserve scaling/Pareto views for ordered resource or trade-off variables; show uncertainty across seeds.",
        "must_observe": ["baseline/control", "changed component", "resource axis", "seed/replicate uncertainty", "dominated vs selected points"],
    },
}


def build_coverage_report(library: Any) -> dict[str, Any]:
    """Measure reviewed references available for every taxonomy family."""
    families: list[dict[str, Any]] = []
    for family_id, spec in FIGURE_FAMILIES.items():
        refs: dict[str, Any] = {}
        for figure_type in spec["figure_types"]:
            for ref in library.query(figure_type=figure_type):
                refs[ref.id] = ref
        ids = sorted(refs)
        families.append({
            "id": family_id,
            "figure_types": spec["figure_types"],
            "candidate_ids": ids[:8],
            "reference_count": len(ids),
            "covered": bool(ids),
        })
    covered = sum(1 for item in families if item["covered"])
    return {
        "family_count": len(families),
        "covered_family_count": covered,
        "missing_families": [item["id"] for item in families if not item["covered"]],
        "families": families,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=str)
    args = parser.parse_args()
    try:
        from .reference_library import ReferenceLibrary
    except ImportError:  # pragma: no cover - direct CLI execution
        from reference_library import ReferenceLibrary
    library = ReferenceLibrary(root=args.skill_root) if args.skill_root else ReferenceLibrary()
    report = build_coverage_report(library)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
