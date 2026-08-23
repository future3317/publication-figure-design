"""L2 structural visual checks at whole/panel/plot/legend scales."""

from __future__ import annotations

from typing import Any, Mapping


def run_structural_qa(figure_metrics: Mapping[str, Any], reference_dna: Mapping[str, Any] | None = None) -> dict[str, Any]:
    metrics = dict(figure_metrics.get("metrics", figure_metrics))
    names = ("layout_topology_similarity", "panel_proportion_similarity", "whitespace_similarity", "legend_annotation_similarity")
    values = {name: float(metrics.get(name, 0.0)) for name in names}
    return {"layer": "L2_structural_visual", "passed": all(value >= 0.68 for value in values.values()), "metrics": values, "scales": ["whole_figure", "panel", "plot", "legend", "annotation"]}
