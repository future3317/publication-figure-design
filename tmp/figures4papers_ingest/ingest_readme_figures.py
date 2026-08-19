# -*- coding: utf-8 -*-
"""Ingest selected figures from the local figures4papers repository into the
publication-figure-design Visual Reference Library.

These are actual publication figures from Chen Liu's figures4papers repo.
They are marked as private_reference by default; change usage_scope if you
own redistribution rights.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from reference_library import ingest_image

FIGURES4PAPERS_ROOT = Path("E:/CODE/figures4papers")

FIGURES = [
    (
        "figure_ImmunoStruct/figures/bars_comparison_IEDB.png",
        "BarComparison",
        {
            "subtype": "figures4papers_comparison_bars",
            "tags": ["figures4papers", "publication-figure", "bar-comparison", "grouped-bar", "IEDB"],
            "journal_style": "Nature",
            "n_groups": 4,
            "data_density": "medium",
            "aesthetic_rating": 4,
        },
    ),
    (
        "figure_Brainteaser/figures/brute_force.png",
        "BarComposition",
        {
            "subtype": "figures4papers_composition_bars",
            "tags": ["figures4papers", "publication-figure", "bar-composition", "stacked-bar", "brute-force"],
            "journal_style": "Nature",
            "n_groups": 5,
            "data_density": "medium",
            "aesthetic_rating": 4,
        },
    ),
    (
        "figure_VIGIL/figures/comparison_radar.png",
        "Radar",
        {
            "subtype": "figures4papers_radar",
            "tags": ["figures4papers", "publication-figure", "radar", "multi-axis", "comparison"],
            "journal_style": "Nature",
            "n_groups": 3,
            "data_density": "low",
            "aesthetic_rating": 4,
        },
    ),
    (
        "figure_VIGIL/figures/comparison_posttraining.png",
        "LineTrend",
        {
            "subtype": "figures4papers_posttraining_trend",
            "tags": ["figures4papers", "publication-figure", "line-trend", "post-training", "multi-curve"],
            "journal_style": "Nature",
            "n_groups": 3,
            "data_density": "medium",
            "aesthetic_rating": 4,
        },
    ),
    (
        "figure_ophthal_review/figures/trend_by_month.png",
        "LineTrend",
        {
            "subtype": "figures4papers_monthly_trend",
            "tags": ["figures4papers", "publication-figure", "line-trend", "time-series", "monthly"],
            "journal_style": "Nature",
            "n_groups": 2,
            "data_density": "medium",
            "aesthetic_rating": 3.5,
        },
    ),
    (
        "figure_ophthal_review/figures/composition_heatmap.png",
        "heatmap",
        {
            "subtype": "figures4papers_composition_heatmap",
            "tags": ["figures4papers", "publication-figure", "heatmap", "composition", "annotation"],
            "journal_style": "Nature",
            "n_groups": 5,
            "data_density": "medium",
            "aesthetic_rating": 4,
        },
    ),
    (
        "figure_RNAGenScape/figures/results_comparison_optimization.png",
        "heatmap",
        {
            "subtype": "figures4papers_optimization_heatmap",
            "tags": ["figures4papers", "publication-figure", "heatmap", "optimization", "comparison"],
            "journal_style": "Nature",
            "n_groups": 4,
            "data_density": "medium",
            "aesthetic_rating": 4,
        },
    ),
    (
        "figure_CellSpliceNet/figures/comparison_human.png",
        "BarComparison",
        {
            "subtype": "figures4papers_human_comparison_bars",
            "tags": ["figures4papers", "publication-figure", "bar-comparison", "grouped-bar", "human"],
            "journal_style": "Nature",
            "n_groups": 3,
            "data_density": "medium",
            "aesthetic_rating": 4,
        },
    ),
    (
        "figure_CellSpliceNet/figures/ablation.png",
        "BarAblation",
        {
            "subtype": "figures4papers_ablation_bars",
            "tags": ["figures4papers", "publication-figure", "ablation", "grouped-bar", "CellSpliceNet"],
            "journal_style": "Nature",
            "n_groups": 4,
            "data_density": "medium",
            "aesthetic_rating": 4,
        },
    ),
    (
        "figure_Cflows/figures/fig2_comparison_Trajectory.png",
        "LineTrend",
        {
            "subtype": "figures4papers_trajectory_comparison",
            "tags": ["figures4papers", "publication-figure", "line-trend", "trajectory", "comparison"],
            "journal_style": "Nature",
            "n_groups": 3,
            "data_density": "high",
            "aesthetic_rating": 4,
        },
    ),
]


def main() -> int:
    for rel_path, figure_type, meta_override in FIGURES:
        image_path = FIGURES4PAPERS_ROOT / rel_path
        if not image_path.exists():
            print(f"SKIP (not found): {rel_path}")
            continue

        meta = {
            "source": "Chen Liu, figures4papers repository",
            "source_url": f"https://github.com/ChenLiu-1996/figures4papers/tree/main/{rel_path}",
            "license": "unknown",
            "usage_scope": "private_reference",
            "review_status": "pending",
            "production_ready": False,
            "palette": None,
            "palette_policy": "preserve",
            "layout": "1x1",
            "notes": f"Publication figure from figures4papers/{rel_path}. Used as visual reference for {figure_type} style; do not redistribute without permission.",
        }
        meta.update(meta_override)

        ref = ingest_image(
            image_path=image_path,
            figure_type=figure_type,
            metadata_override=meta,
        )
        print(f"Ingested {ref.id}: {figure_type} <- {rel_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
