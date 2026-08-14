#!/usr/bin/env python3
"""Build independent visual-grammar reconstructions from audited figure sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon
from PIL import Image

try:
    from .reference_library import ReferenceLibrary
except ImportError:  # pragma: no cover - standalone CLI
    from reference_library import ReferenceLibrary


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}
MANIFEST_RELATIVE_PATH = Path("assets/visual-references/source-reconstruction-manifest.json")
EXPECTED_COUNTS = {"nature-figure": 15, "figures4papers": 39, "total": 54}
RENDERER_VERSION = 3
PALETTES = (
    ("#35618f", "#79a8a9", "#e5a84b", "#c96558", "#7868a6"),
    ("#274c77", "#6096ba", "#a3cef1", "#e7b566", "#bc6c64"),
    ("#26547c", "#06a77d", "#f1a208", "#d95d39", "#6b5ca5"),
    ("#3d5a80", "#98c1d9", "#ee6c4d", "#7a9e7e", "#c9ada7"),
)


@dataclass(frozen=True)
class SourceFigure:
    repository: str
    relative_path: str
    source_sha256: str
    width: int
    height: int
    license_class: str
    source_action: str
    visual_family: str
    source_path: Path

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("source_path")
        return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _image_paths(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def classify_visual_family(relative_path: str) -> str:
    """Classify a source from observable filename/path semantics."""
    text = relative_path.lower().replace("_", "-")
    name = Path(text).name
    if "radar" in text or "polar" in text:
        return "radar_grid"
    if "swiss-roll" in text or "manifold" in text:
        return "manifold_3d"
    if "heatmap" in text or "composition" in text:
        return "heatmap_grid"
    if "spatial-imaging" in text or "image-plates" in text:
        return "spatial_image_plate"
    if "network-matrix" in text:
        return "network_matrix"
    if "scatter-bubble" in text:
        return "scatter_bubble"
    if "distribution" in text or "distillation" in text:
        return "distribution_grid"
    if "forest-interval" in text:
        return "forest_interval"
    if "area-stacked" in text:
        return "area_stacked"
    if "line-trends" in text or any(token in text for token in ("trend", "sweep", "curves", "posttraining")):
        return "line_grid"
    if "bar-charts" in text or any(token in text for token in ("bars-", "ablation", "correctness", "brute-force", "rewriting", "selfcorrection")):
        return "grouped_bar"
    if any(token in text for token in ("schematic", "concept", "idea", "illustration", "motivation", "teaser")):
        return "mechanism_schematic"
    if any(token in text for token in ("comparison", "results-", "observation")):
        return "comparison_composite"
    if "material-mechanism" in text:
        return "material_mechanism"
    if "in-vivo" in text:
        return "in_vivo_efficacy"
    if "single-cell" in text:
        return "single_cell_systems"
    if "validation-perturbation" in text:
        return "validation_perturbation"
    return "comparison_composite"


def visual_profile(record: SourceFigure) -> dict[str, Any]:
    """Return observable topology and density rather than style tokens alone."""
    text = record.relative_path.lower().replace("_", "-")
    name = Path(text).name
    if "chart-atlas" in text:
        grid = [4, 4]
    elif "assets/gallery/fig2-" in text:
        grid = [3, 5]
    elif "assets/gallery/" in text:
        grid = [3, 4]
    elif name == "dispersion-observation.png":
        grid = [3, 4]
    elif any(token in name for token in ("immunostruct-results", "correctness-by-subcategory")):
        grid = [3, 4]
    elif name in {"brute-force.png", "selfcorrection-math.png", "correctness-by-category.png"}:
        grid = [2, 4]
    elif any(token in name for token in ("schematic", "contrastive")):
        grid = [2, 3]
    elif name in {"rewriting.png", "diffusion-swiss-roll.png", "trend-by-month.png", "results-comparison-optimization.png", "results-sweep.png", "concept.png"}:
        grid = [1, 2]
    elif any(token in name for token in ("bars-", "comparison-human", "comparison-worm", "fig2-comparison", "figx-comparison", "ablation-curves")):
        grid = [1, 3]
    elif record.width / max(record.height, 1) > 2.4:
        grid = [1, 3]
    elif record.width / max(record.height, 1) > 1.35:
        grid = [1, 2]
    else:
        grid = [1, 1]
    panel_count = grid[0] * grid[1]
    return {
        "panel_grid": grid,
        "panel_count": panel_count,
        "aspect_class": "wide" if record.width > record.height * 1.35 else "tall" if record.height > record.width * 1.2 else "balanced",
        "density": "high" if panel_count >= 8 else "medium" if panel_count >= 3 else "focused",
        "visual_family": record.visual_family,
    }


def _blueprint(
    blueprint_id: str,
    mosaic: tuple[str, ...],
    recipes: dict[str, str],
    observation: str,
) -> dict[str, Any]:
    """Declare the observable structure that an independent redraw must preserve."""
    slots = []
    for row in mosaic:
        for slot in row:
            if slot != "." and slot not in slots:
                slots.append(slot)
    missing = [slot for slot in slots if slot not in recipes]
    if missing:
        raise ValueError(f"{blueprint_id}: no panel recipe for {missing}")
    return {
        "blueprint_id": blueprint_id,
        "mosaic": list(mosaic),
        "panel_recipes": [{"id": slot, "kind": recipes[slot]} for slot in slots],
        "annotation_model": "panel_letters + local_legends + direct_callouts",
        "source_observation": observation,
    }


# These blueprints are intentionally source-specific.  A family label such as
# ``grouped_bar`` is useful for retrieval, but it is not enough information to
# reproduce the topology of a particular manuscript figure.
SOURCE_BLUEPRINTS: dict[str, dict[str, Any]] = {
    "assets/Dispersion_motivation.png": _blueprint("dispersion_motivation", ("AABB", "CCDD"), {"A": "schematic:inputs", "B": "diagram:latent", "C": "scatter:embedding", "D": "line:dispersion"}, "four-stage motivation: inputs, latent-space idea, embedding, and response curve"),
    "assets/Dispersion_observation.png": _blueprint("dispersion_observation", ("AABB", "CCDD", "EEFF"), {"A": "schematic:observation", "B": "scatter:groups", "C": "heatmap:correlation", "D": "line:comparison", "E": "distribution:ridge", "F": "forest:effects"}, "asymmetric observation figure with one explanatory panel and five evidence panels"),
    "assets/Dispersion_observation_distillation.png": _blueprint("dispersion_observation_distillation", ("ABC", "DEF"), {"A": "distribution:hist", "B": "distribution:violin", "C": "distribution:ridge", "D": "scatter:groups", "E": "line:distillation", "F": "bar:summary"}, "six compact distribution and comparison panels"),
    "assets/ImmunoStruct_contrastive.png": _blueprint("immunostruct_contrastive", ("AABB", "CCDD"), {"A": "schematic:contrastive", "B": "diagram:pairing", "C": "scatter:embedding", "D": "bar:contrast"}, "paired contrastive workflow followed by embedding and quantitative comparison"),
    "assets/ImmunoStruct_results_CEDAR.png": _blueprint("immunostruct_results_cedar", ("ABCD", "EFGH"), {"A": "bar:comparison", "B": "bar:ablation", "C": "line:calibration", "D": "heatmap:matrix", "E": "distribution:violin", "F": "scatter:groups", "G": "forest:effects", "H": "table:metrics"}, "eight-panel benchmark result grid with mixed evidence types"),
    "assets/ImmunoStruct_results_IEDB.png": _blueprint("immunostruct_results_iedb", ("ABCD", "EFGH"), {"A": "bar:comparison", "B": "bar:ablation", "C": "line:calibration", "D": "heatmap:matrix", "E": "distribution:violin", "F": "scatter:groups", "G": "forest:effects", "H": "table:metrics"}, "eight-panel benchmark result grid, distinct IEDB rendering"),
    "assets/ImmunoStruct_schematic.png": _blueprint("immunostruct_schematic", ("AAAB", "CCCB"), {"A": "schematic:architecture", "B": "diagram:attention", "C": "diagram:training"}, "wide architecture panel with two subordinate explanatory branches"),
    "assets/RNAGenScape_schematic.png": _blueprint("rnagenscape_schematic", ("AABB", "CCDD"), {"A": "schematic:generator", "B": "diagram:conditioning", "C": "manifold:latent", "D": "spatial:expression"}, "generative pipeline with latent-space and spatial readouts"),
    "assets/RNAGenScape_teaser.png": _blueprint("rnagenscape_teaser", ("AABB",), {"A": "diagram:cells", "B": "spatial:expression"}, "two-part teaser: cell representation to spatial expression"),
    "assets/VIGIL_teaser.png": _blueprint("vigil_teaser", ("AABB",), {"A": "schematic:temporal", "B": "line:forecast"}, "temporal method teaser paired with a predicted trajectory"),
    "figure_Brainteaser/figures/brute_force.png": _blueprint("brainteaser_brute_force", ("AABB", "CCDD"), {"A": "bar:composition", "B": "bar:comparison", "C": "distribution:points", "D": "table:metrics"}, "composition bars, comparison bars, raw observations, and summary table"),
    "figure_Brainteaser/figures/correctness_by_category.png": _blueprint("brainteaser_correctness_category", ("AB", "CD"), {"A": "bar:category", "B": "bar:category", "C": "distribution:points", "D": "forest:effects"}, "category-level correctness panels with raw and interval evidence"),
    "figure_Brainteaser/figures/correctness_by_subcategory.png": _blueprint("brainteaser_correctness_subcategory", ("ABC", "DEF", "GHI"), {"A": "bar:category", "B": "bar:category", "C": "bar:category", "D": "bar:category", "E": "bar:category", "F": "bar:category", "G": "distribution:points", "H": "forest:effects", "I": "table:metrics"}, "dense subcategory comparison grid with six categorical panels"),
    "figure_Brainteaser/figures/rewriting.png": _blueprint("brainteaser_rewriting", ("ABC",), {"A": "bar:beforeafter", "B": "scatter:paired", "C": "distribution:violin"}, "before/after rewriting comparison with paired observation panel"),
    "figure_Brainteaser/figures/selfcorrection_math.png": _blueprint("brainteaser_selfcorrection_math", ("ABCD", "EFGH"), {"A": "bar:category", "B": "bar:category", "C": "bar:category", "D": "bar:category", "E": "line:iterations", "F": "scatter:paired", "G": "distribution:points", "H": "table:metrics"}, "dense self-correction grid: categorical gains, iterations, paired observations, and metrics"),
    "figure_CellSpliceNet/figures/ablation.png": _blueprint("cellsplicenet_ablation", ("AAB", "CCD"), {"A": "bar:ablation", "B": "line:training", "C": "distribution:violin", "D": "table:metrics"}, "ablation hero panel supported by training, distribution, and metric panels"),
    "figure_CellSpliceNet/figures/comparison_human.png": _blueprint("cellsplicenet_comparison_human", ("ABC",), {"A": "bar:comparison", "B": "heatmap:matrix", "C": "line:calibration"}, "three-panel human benchmark: methods, matrix evidence, and calibration"),
    "figure_CellSpliceNet/figures/comparison_worm.png": _blueprint("cellsplicenet_comparison_worm", ("ABC",), {"A": "bar:comparison", "B": "heatmap:matrix", "C": "line:calibration"}, "three-panel worm benchmark: methods, matrix evidence, and calibration"),
    "figure_Cflows/figures/diffusion_swiss_roll.png": _blueprint("cflows_diffusion_swiss_roll", ("AABB",), {"A": "manifold:source", "B": "manifold:flow"}, "paired manifold views showing source geometry and transformed geometry"),
    "figure_Cflows/figures/fig2_comparison_GeneRegulatory.png": _blueprint("cflows_gene_regulatory", ("ABC",), {"A": "network:regulatory", "B": "scatter:trajectory", "C": "line:dynamics"}, "network topology, state-space trajectory, and temporal dynamics"),
    "figure_Cflows/figures/fig2_comparison_Trajectory.png": _blueprint("cflows_trajectory", ("ABC",), {"A": "scatter:trajectory", "B": "line:dynamics", "C": "forest:effects"}, "trajectory panel followed by dynamics and effect comparison"),
    "figure_Cflows/figures/figX_comparison_Ablation.png": _blueprint("cflows_ablation", ("ABC",), {"A": "bar:ablation", "B": "line:training", "C": "table:metrics"}, "ablation bars with learning curve and metric table"),
    "figure_Dispersion/figures/idea.png": _blueprint("dispersion_idea", ("AABB",), {"A": "schematic:idea", "B": "diagram:geometry"}, "conceptual idea paired with geometric explanation"),
    "figure_Dispersion/figures/illustration.png": _blueprint("dispersion_illustration", ("AABB",), {"A": "diagram:geometry", "B": "schematic:process"}, "geometric illustration and process schematic"),
    "figure_ImmunoStruct/figures/bars_ablation_Cancer.png": _blueprint("immunostruct_ablation_cancer", ("ABC",), {"A": "bar:ablation", "B": "bar:ablation", "C": "distribution:points"}, "three cancer ablation panels with replicate observations"),
    "figure_ImmunoStruct/figures/bars_ablation_IEDB.png": _blueprint("immunostruct_ablation_iedb", ("ABC",), {"A": "bar:ablation", "B": "bar:ablation", "C": "distribution:points"}, "three IEDB ablation panels with replicate observations"),
    "figure_ImmunoStruct/figures/bars_comparison_Cancer.png": _blueprint("immunostruct_comparison_cancer", ("ABC",), {"A": "bar:comparison", "B": "bar:comparison", "C": "forest:effects"}, "cancer method comparison with interval panel"),
    "figure_ImmunoStruct/figures/bars_comparison_IEDB.png": _blueprint("immunostruct_comparison_iedb", ("ABC",), {"A": "bar:comparison", "B": "bar:comparison", "C": "forest:effects"}, "IEDB method comparison with interval panel"),
    "figure_ophthal_review/figures/composition_heatmap.png": _blueprint("ophthal_composition_heatmap", ("AABB", "CCDD"), {"A": "heatmap:composition", "B": "heatmap:matrix", "C": "bar:composition", "D": "forest:effects"}, "heatmap hero with matrix, composition, and interval support"),
    "figure_ophthal_review/figures/trend_by_month.png": _blueprint("ophthal_monthly_trend", ("AB", "CD"), {"A": "line:monthly", "B": "line:monthly", "C": "area:composition", "D": "bar:summary"}, "monthly trends, composition over time, and summary comparison"),
    "figure_RNAGenScape/figures/manifold.png": _blueprint("rnagenscape_manifold", ("AB",), {"A": "manifold:source", "B": "manifold:generated"}, "paired manifold rendering of source and generated distributions"),
    "figure_RNAGenScape/figures/manifold_holes.png": _blueprint("rnagenscape_manifold_holes", ("ABC",), {"A": "manifold:source", "B": "manifold:holes", "C": "manifold:generated"}, "three manifold states emphasizing holes and generated coverage"),
    "figure_RNAGenScape/figures/results_comparison_optimization.png": _blueprint("rnagenscape_optimization", ("AABB", "CCDD"), {"A": "heatmap:optimization", "B": "line:optimization", "C": "bar:comparison", "D": "scatter:embedding"}, "optimization landscape hero with trajectory, method comparison, and embedding"),
    "figure_RNAGenScape/figures/results_comparison_speed.png": _blueprint("rnagenscape_speed", ("AB",), {"A": "bar:comparison", "B": "forest:effects"}, "speed comparison with effect-size intervals"),
    "figure_RNAGenScape/figures/results_sweep.png": _blueprint("rnagenscape_sweep", ("AB",), {"A": "line:sweep", "B": "line:sweep"}, "paired parameter-sweep curves"),
    "figure_VIGIL/figures/ablation_curves.png": _blueprint("vigil_ablation_curves", ("ABC",), {"A": "line:ablation", "B": "line:ablation", "C": "line:ablation"}, "three ablation learning curves with uncertainty bands"),
    "figure_VIGIL/figures/comparison_posttraining.png": _blueprint("vigil_posttraining", ("ABC",), {"A": "line:posttraining", "B": "line:posttraining", "C": "line:posttraining"}, "three post-training comparison curves"),
    "figure_VIGIL/figures/comparison_radar.png": _blueprint("vigil_radar_comparison", ("AB",), {"A": "radar:methods", "B": "radar:methods"}, "paired polar method comparisons"),
    "figure_VIGIL/figures/concept.png": _blueprint("vigil_concept", ("AABB",), {"A": "schematic:temporal", "B": "diagram:forecast"}, "temporal concept sketch with forecast explanation"),
    "assets/chart-atlas/atlas-01-bar-charts.png": _blueprint("atlas_bar_charts", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "bar:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 bar-chart variants arranged as an atlas"),
    "assets/chart-atlas/atlas-02-line-trends.png": _blueprint("atlas_line_trends", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "line:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 trend and uncertainty variants arranged as an atlas"),
    "assets/chart-atlas/atlas-03-heatmaps.png": _blueprint("atlas_heatmaps", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "heatmap:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 matrix and annotation variants arranged as an atlas"),
    "assets/chart-atlas/atlas-04-scatter-bubble.png": _blueprint("atlas_scatter_bubble", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "scatter:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 scatter and bubble variants arranged as an atlas"),
    "assets/chart-atlas/atlas-05-radar-polar.png": _blueprint("atlas_radar_polar", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "radar:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 polar-chart variants arranged as an atlas"),
    "assets/chart-atlas/atlas-06-distributions.png": _blueprint("atlas_distributions", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "distribution:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 distribution variants arranged as an atlas"),
    "assets/chart-atlas/atlas-07-forest-interval.png": _blueprint("atlas_forest_interval", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "forest:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 interval and effect-size variants arranged as an atlas"),
    "assets/chart-atlas/atlas-08-area-stacked.png": _blueprint("atlas_area_stacked", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "area:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 stacked-area and composition variants arranged as an atlas"),
    "assets/chart-atlas/atlas-09-image-plates.png": _blueprint("atlas_image_plates", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "spatial:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 spatial/image-plate variants arranged as an atlas"),
    "assets/chart-atlas/atlas-10-network-matrix.png": _blueprint("atlas_network_matrix", ("ABCD", "EFGH", "IJKL", "MNOP"), {slot: "network:atlas" for slot in "ABCDEFGHIJKLMNOP"}, "16 network/matrix variants arranged as an atlas"),
    "assets/gallery/fig1-material-mechanism-rich.png": _blueprint("gallery_material_mechanism", ("AABB", "CDDE"), {"A": "schematic:materials", "B": "diagram:mechanism", "C": "spatial:micrograph", "D": "line:response", "E": "bar:comparison"}, "asymmetric material mechanism figure with large mechanism hero"),
    "assets/gallery/fig2-spatial-imaging-rich.png": _blueprint("gallery_spatial_imaging", ("ABCD", "EFGH", "IJKL"), {"A": "spatial:sample", "B": "spatial:mask", "C": "spatial:overlay", "D": "spatial:zoom", "E": "spatial:sample", "F": "spatial:mask", "G": "spatial:overlay", "H": "spatial:zoom", "I": "spatial:zoom", "J": "scatter:spots", "K": "heatmap:matrix", "L": "bar:summary"}, "image-plate workflow with sample, mask, overlay, zoom, and quantitative support"),
    "assets/gallery/fig3-in-vivo-efficacy-rich.png": _blueprint("gallery_in_vivo_efficacy", ("AABB", "CCDE"), {"A": "schematic:treatment", "B": "line:efficacy", "C": "spatial:imaging", "D": "bar:response", "E": "survival:curve"}, "in-vivo study: treatment schematic, longitudinal efficacy, imaging, response, survival"),
    "assets/gallery/fig4-single-cell-systems-rich.png": _blueprint("gallery_single_cell_systems", ("AABB", "CCDE"), {"A": "schematic:singlecell", "B": "scatter:umap", "C": "heatmap:markers", "D": "distribution:violin", "E": "line:trajectory"}, "single-cell system figure with workflow, embedding hero, markers, distributions, trajectory"),
    "assets/gallery/fig5-validation-perturbation-rich.png": _blueprint("gallery_validation_perturbation", ("AABB", "CCDE"), {"A": "schematic:perturbation", "B": "scatter:validation", "C": "bar:ablation", "D": "heatmap:response", "E": "forest:effects"}, "perturbation workflow and validation evidence across scatter, ablation, matrix, interval panels"),
}


def reconstruction_blueprint(record: SourceFigure) -> dict[str, Any]:
    """Return the source-specific visual grammar, never a family-wide template."""
    blueprint = SOURCE_BLUEPRINTS.get(record.relative_path)
    if blueprint is None:
        raise KeyError(f"No source-specific reconstruction blueprint for {record.relative_path}")
    return json.loads(json.dumps(blueprint))


def discover_sources(nature_root: Path | str, figures_root: Path | str) -> list[SourceFigure]:
    nature_root = Path(nature_root)
    figures_root = Path(figures_root)
    if not nature_root.is_dir():
        raise FileNotFoundError(f"nature-figure root not found: {nature_root}")
    if not figures_root.is_dir():
        raise FileNotFoundError(f"figures4papers root not found: {figures_root}")

    selected: list[tuple[str, Path, Path, str, str]] = []
    for path in _image_paths(nature_root):
        relative = path.relative_to(nature_root)
        if relative.parts[:2] == ("assets", "figures4papers"):
            continue
        selected.append(("nature-figure", nature_root, path, "Apache-2.0", "licensed_visual_source"))
    for path in _image_paths(figures_root):
        selected.append(("figures4papers", figures_root, path, "unknown", "independent_reconstruction"))

    records: list[SourceFigure] = []
    for repository, root, path, license_class, action in selected:
        previous_pixel_limit = Image.MAX_IMAGE_PIXELS
        try:
            Image.MAX_IMAGE_PIXELS = None
            with Image.open(path) as image:
                width, height = image.size
        finally:
            Image.MAX_IMAGE_PIXELS = previous_pixel_limit
        relative = path.relative_to(root).as_posix()
        records.append(
            SourceFigure(
                repository=repository,
                relative_path=relative,
                source_sha256=_sha256(path),
                width=width,
                height=height,
                license_class=license_class,
                source_action=action,
                visual_family=classify_visual_family(relative),
                source_path=path,
            )
        )

    hashes = [record.source_sha256 for record in records]
    if len(hashes) != len(set(hashes)):
        raise ValueError("Selected source collection contains duplicate image fingerprints.")
    return sorted(records, key=lambda item: (item.repository, item.relative_path.lower()))


def _style(seed: int) -> tuple[np.random.Generator, tuple[str, ...]]:
    return np.random.default_rng(seed), PALETTES[seed % len(PALETTES)]


def _clean_axis(ax: plt.Axes, grid: bool = True) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=6, length=2, width=0.6, colors="#3d4650")
    if grid:
        ax.grid(axis="y", color="#d7dde2", linewidth=0.45, alpha=0.75, zorder=0)
    ax.set_axisbelow(True)


def _panel_label(ax: plt.Axes, label: str) -> None:
    ax.text2D(-0.13, 1.08, label, transform=ax.transAxes, fontsize=9, fontweight="bold", va="top") if hasattr(ax, "text2D") else ax.text(-0.13, 1.08, label, transform=ax.transAxes, fontsize=9, fontweight="bold", va="top")


def _grouped_bar(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(1, 2)
    for p, ax in enumerate(np.ravel(axes)):
        n, groups = 5 + p, 3
        x = np.arange(n)
        base = 0.45 + 0.2 * rng.random(n)
        for group in range(groups):
            values = np.clip(base + (group - 1) * 0.08 + rng.normal(0, 0.035, n), 0.12, 0.95)
            ax.bar(x + (group - 1) * 0.23, values, 0.21, color=colors[group], edgecolor="white", linewidth=0.4)
        ax.set_xticks(x, [f"C{i + 1}" for i in x])
        ax.set_ylim(0, 1.05)
        _clean_axis(ax)
        _panel_label(ax, chr(65 + p))


def _line_grid(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(2, 2)
    x = np.linspace(0, 1, 9)
    for p, ax in enumerate(np.ravel(axes)):
        for group in range(3):
            direction = 1 if (p + group) % 3 else -0.35
            y = 0.25 + 0.12 * group + direction * 0.38 * x + np.cumsum(rng.normal(0, 0.018, x.size))
            err = 0.018 + 0.012 * rng.random(x.size)
            ax.plot(x, y, color=colors[group], marker=("o", "s", "^")[group], ms=2.6, lw=1.2)
            ax.fill_between(x, y - err, y + err, color=colors[group], alpha=0.12, linewidth=0)
        _clean_axis(ax)
        _panel_label(ax, chr(65 + p))


def _heatmap_grid(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(1, 3, gridspec_kw={"width_ratios": [1, 1, 0.8]})
    for p, ax in enumerate(axes[:2]):
        matrix = rng.normal(size=(8, 7)) + np.linspace(-0.8, 0.8, 8)[:, None] * (1 if p == 0 else -1)
        image = ax.imshow(matrix, cmap="RdBu_r", vmin=-2.2, vmax=2.2, aspect="auto")
        ax.set_xticks(range(7), [f"S{i + 1}" for i in range(7)], rotation=45, ha="right", fontsize=5)
        ax.set_yticks(range(8), [f"G{i + 1}" for i in range(8)], fontsize=5)
        _panel_label(ax, chr(65 + p))
    ax = axes[2]
    means = rng.normal(0, 0.7, 8)
    ax.errorbar(means, np.arange(8), xerr=0.15 + rng.random(8) * 0.12, fmt="o", color=colors[0], ecolor="#7d8790", ms=3)
    ax.axvline(0, color="#59636c", lw=0.7)
    ax.set_yticks(np.arange(8), [])
    _clean_axis(ax, grid=False)
    _panel_label(ax, "C")
    fig.colorbar(image, ax=list(axes[:2]), shrink=0.55, pad=0.02)


def _scatter_bubble(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(1, 2)
    for p, ax in enumerate(axes):
        for group in range(3):
            center = np.array([group * 1.4, (group + p) % 3 * 0.9])
            points = rng.normal(center, [0.35, 0.28], (45, 2))
            sizes = rng.uniform(9, 48, len(points))
            ax.scatter(points[:, 0], points[:, 1], s=sizes, c=colors[group], alpha=0.62, linewidth=0.25, edgecolor="white")
        _clean_axis(ax, grid=False)
        _panel_label(ax, chr(65 + p))


def _radar_grid(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    fig.clear()
    axes = [fig.add_subplot(1, 2, i + 1, projection="polar") for i in range(2)]
    angles = np.linspace(0, 2 * np.pi, 7, endpoint=False)
    closed = np.r_[angles, angles[0]]
    for p, ax in enumerate(axes):
        for group in range(3):
            values = np.clip(0.42 + 0.13 * group + rng.normal(0, 0.09, 7), 0.12, 0.95)
            values = np.r_[values, values[0]]
            ax.plot(closed, values, color=colors[group], lw=1.1)
            ax.fill(closed, values, color=colors[group], alpha=0.08)
        ax.set_xticks(angles, [f"M{i + 1}" for i in range(7)], fontsize=5)
        ax.set_yticklabels([])
        ax.set_ylim(0, 1)
        ax.grid(color="#d7dde2", lw=0.45)
        _panel_label(ax, chr(65 + p))


def _distribution_grid(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(1, 3)
    for group in range(3):
        data = rng.normal(group * 0.7, 0.65 + group * 0.08, 220)
        axes[0].hist(data, bins=18, density=True, histtype="stepfilled", alpha=0.35, color=colors[group])
    groups = [rng.normal(i * 0.25, 0.4, 65) for i in range(4)]
    violin = axes[1].violinplot(groups, showmedians=True, widths=0.8)
    for body, color in zip(violin["bodies"], colors):
        body.set_facecolor(color); body.set_alpha(0.6); body.set_edgecolor("white")
    for row in range(5):
        data = rng.normal(row * 0.6, 0.42, 150)
        counts, edges = np.histogram(data, bins=35, density=True)
        centers = (edges[:-1] + edges[1:]) / 2
        axes[2].fill_between(centers, row, row + counts * 0.38, color=colors[row % len(colors)], alpha=0.7)
    for p, ax in enumerate(axes):
        _clean_axis(ax, grid=False); _panel_label(ax, chr(65 + p))


def _forest_interval(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(1, 2)
    for p, ax in enumerate(axes):
        y = np.arange(9)
        effect = rng.normal(0.12 * (p * 2 - 1), 0.3, len(y))
        err = rng.uniform(0.12, 0.32, len(y))
        ax.errorbar(effect, y, xerr=err, fmt="o", color=colors[p], ecolor="#77838c", ms=3, capsize=1.5)
        ax.axvline(0, color="#4c5963", lw=0.7, ls="--")
        ax.set_yticks(y, [f"Study {i + 1}" for i in y], fontsize=5)
        _clean_axis(ax, grid=False); _panel_label(ax, chr(65 + p))


def _area_stacked(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(2, 1)
    x = np.arange(18)
    for p, ax in enumerate(axes):
        raw = rng.gamma(2.2, 1, (4, len(x)))
        smooth = np.array([np.convolve(row, np.ones(3) / 3, mode="same") for row in raw])
        values = smooth / smooth.sum(axis=0)
        ax.stackplot(x, values, colors=colors[:4], alpha=0.82, linewidth=0.35, edgecolor="white")
        ax.set_ylim(0, 1); _clean_axis(ax, grid=False); _panel_label(ax, chr(65 + p))


def _synthetic_field(rng: np.random.Generator, size: int = 120) -> np.ndarray:
    yy, xx = np.mgrid[-1:1:complex(size), -1:1:complex(size)]
    field = np.zeros_like(xx)
    for _ in range(9):
        cx, cy = rng.uniform(-0.8, 0.8, 2)
        sigma = rng.uniform(0.05, 0.22)
        field += rng.uniform(0.5, 1.2) * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma**2))
    return field + rng.normal(0, 0.035, field.shape)


def _spatial_image_plate(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(2, 3)
    for p, ax in enumerate(np.ravel(axes)):
        field = _synthetic_field(rng)
        cmap = ("magma", "viridis", "cividis")[p % 3]
        ax.imshow(field, cmap=cmap)
        if p % 2:
            spots = rng.uniform(5, 115, (24, 2))
            ax.scatter(spots[:, 0], spots[:, 1], s=4, facecolors="none", edgecolors="white", linewidths=0.35)
        ax.plot([8, 32], [108, 108], color="white", lw=2)
        ax.set_axis_off(); _panel_label(ax, chr(65 + p))


def _network_matrix(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(1, 2)
    ax = axes[0]
    theta = np.linspace(0, 2 * np.pi, 11, endpoint=False)
    nodes = np.c_[np.cos(theta), np.sin(theta)]
    for _ in range(20):
        a, b = rng.choice(len(nodes), 2, replace=False)
        ax.plot(nodes[[a, b], 0], nodes[[a, b], 1], color="#aeb7bd", lw=0.45, zorder=0)
    ax.scatter(nodes[:, 0], nodes[:, 1], c=[colors[i % 4] for i in range(len(nodes))], s=45, edgecolor="white", lw=0.6)
    ax.set_axis_off(); ax.set_aspect("equal"); _panel_label(ax, "A")
    matrix = rng.uniform(0, 1, (11, 11)); matrix = (matrix + matrix.T) / 2; np.fill_diagonal(matrix, 1)
    axes[1].imshow(matrix, cmap="Blues", vmin=0, vmax=1)
    axes[1].set_xticks([]); axes[1].set_yticks([]); _panel_label(axes[1], "B")


def _manifold_3d(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    fig.clear()
    axes = [fig.add_subplot(1, 2, i + 1, projection="3d") for i in range(2)]
    t = 1.5 * np.pi * (1 + 2 * rng.random(420))
    x = t * np.cos(t); z = t * np.sin(t); y = rng.uniform(-8, 8, len(t))
    for p, ax in enumerate(axes):
        noise = rng.normal(0, 0.35 + p * 0.2, (3, len(t)))
        ax.scatter(x + noise[0], y + noise[1], z + noise[2], c=t, cmap="viridis", s=4, alpha=0.75, linewidth=0)
        ax.view_init(22 + p * 8, -58 + p * 32)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
        ax.grid(False); _panel_label(ax, chr(65 + p))


def _mechanism_schematic(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    ax = fig.subplots(1, 1)
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.set_axis_off()
    positions = [(1.5, 3.8), (4, 3.8), (6.5, 3.8), (8.7, 3.8)]
    labels = ("Input", "Representation", "Interaction", "Outcome")
    for i, ((x, y), label) in enumerate(zip(positions, labels)):
        box = FancyBboxPatch((x - 0.8, y - 0.55), 1.6, 1.1, boxstyle="round,pad=0.08", fc=colors[i], ec="white", lw=1, alpha=0.88)
        ax.add_patch(box); ax.text(x, y, label, ha="center", va="center", fontsize=7, color="white", fontweight="bold")
        if i < len(positions) - 1:
            ax.add_patch(FancyArrowPatch((x + 0.85, y), (positions[i + 1][0] - 0.85, y), arrowstyle="-|>", mutation_scale=10, color="#55616b", lw=0.9))
    for i in range(12):
        cx, cy = rng.uniform(1, 9), rng.uniform(0.8, 2.2)
        ax.add_patch(Circle((cx, cy), rng.uniform(0.08, 0.2), fc=colors[i % 4], ec="white", lw=0.4, alpha=0.7))
    ax.text(0.2, 5.7, "A", fontsize=10, fontweight="bold", va="top")
    ax.plot([0.5, 9.5], [2.65, 2.65], color="#d7dde2", lw=0.8)


def _comparison_composite(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    axes = fig.subplots(2, 2)
    _grouped_bar_in_axis(axes[0, 0], rng, colors)
    _line_in_axis(axes[0, 1], rng, colors)
    matrix = rng.normal(size=(7, 8))
    axes[1, 0].imshow(matrix, cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
    axes[1, 0].set_xticks([]); axes[1, 0].set_yticks([])
    for group in range(3):
        points = rng.normal([group, 0.35 + group * 0.22], [0.16, 0.08], (32, 2))
        axes[1, 1].scatter(points[:, 0], points[:, 1], s=10, color=colors[group], alpha=0.65, edgecolor="white", lw=0.25)
    _clean_axis(axes[1, 1], grid=False)
    for p, ax in enumerate(np.ravel(axes)): _panel_label(ax, chr(65 + p))


def _grouped_bar_in_axis(ax: plt.Axes, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    x = np.arange(5)
    for group in range(3):
        ax.bar(x + (group - 1) * 0.22, rng.uniform(0.35, 0.9, 5), 0.2, color=colors[group], edgecolor="white", lw=0.35)
    ax.set_xticks(x, [f"C{i + 1}" for i in x]); _clean_axis(ax)


def _line_in_axis(ax: plt.Axes, rng: np.random.Generator, colors: tuple[str, ...]) -> None:
    x = np.arange(9)
    for group in range(3):
        y = 0.25 + group * 0.1 + np.cumsum(rng.normal(0.035, 0.025, len(x)))
        ax.plot(x, y, color=colors[group], marker="o", ms=2, lw=1.1)
    _clean_axis(ax)


def _rich_composite(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...], variant: str) -> None:
    axes = fig.subplot_mosaic([["A", "B", "B"], ["C", "D", "E"]], width_ratios=[1, 1, 1])
    ax = axes["A"]
    ax.set_axis_off()
    for i, x in enumerate((0.18, 0.5, 0.82)):
        ax.add_patch(Circle((x, 0.58), 0.13, transform=ax.transAxes, fc=colors[i], ec="white", lw=0.7, alpha=0.85))
        if i < 2:
            ax.annotate("", (x + 0.19, 0.58), (x + 0.13, 0.58), xycoords="axes fraction", arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "#59636c"})
    field = _synthetic_field(rng, 100)
    axes["B"].imshow(field, cmap="magma"); axes["B"].set_axis_off()
    _grouped_bar_in_axis(axes["C"], rng, colors)
    _line_in_axis(axes["D"], rng, colors)
    cloud = rng.normal(size=(85, 2)) @ np.array([[0.75, 0.15], [-0.08, 0.35]])
    axes["E"].scatter(cloud[:, 0], cloud[:, 1], c=np.linspace(0, 1, len(cloud)), cmap="viridis", s=10, alpha=0.7, linewidth=0)
    _clean_axis(axes["E"], grid=False)
    for label, ax in axes.items(): _panel_label(ax, label)
    fig.text(0.5, 0.01, variant.replace("_", " ").title(), ha="center", fontsize=6, color="#65717b")


def _mini_panel(ax: plt.Axes, family: str, rng: np.random.Generator, colors: tuple[str, ...], index: int) -> None:
    kind = index % 4
    if family == "grouped_bar" or kind == 0:
        x = np.arange(4)
        values = rng.uniform(0.25, 0.9, (3, len(x)))
        for group in range(3):
            ax.bar(x + (group - 1) * 0.2, values[group], 0.19, color=colors[group], linewidth=0)
        ax.set_xticks([]); _clean_axis(ax)
    elif family in {"heatmap_grid", "network_matrix"} or kind == 1:
        ax.imshow(rng.normal(size=(6, 6)), cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
        ax.set_xticks([]); ax.set_yticks([])
    elif family in {"spatial_image_plate", "material_mechanism"} or kind == 2:
        ax.imshow(_synthetic_field(rng, 60), cmap=("magma", "viridis", "cividis")[index % 3])
        ax.set_axis_off()
    else:
        x = np.linspace(0, 1, 8)
        for group in range(3):
            y = 0.2 + group * 0.12 + np.cumsum(rng.normal(0.04, 0.025, len(x)))
            ax.plot(x, y, color=colors[group], lw=0.9)
        _clean_axis(ax)
    _panel_label(ax, chr(65 + index))


def _topology_grid(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...], spec: dict[str, Any]) -> None:
    rows, columns = spec["observable_visual_grammar"]["panel_grid"]
    axes = np.atleast_1d(fig.subplots(rows, columns)).reshape(rows, columns)
    family = spec["visual_family"]
    for index, ax in enumerate(axes.flat):
        _mini_panel(ax, family, rng, colors, index)


def _draw_panel_kind(
    ax: plt.Axes,
    kind: str,
    rng: np.random.Generator,
    colors: tuple[str, ...],
    index: int,
) -> None:
    """Draw one semantic panel recipe using synthetic data and original code."""
    family, _, variant = kind.partition(":")
    variant_seed = sum(ord(char) for char in variant) + index * 17
    local = np.random.default_rng(rng.integers(0, 2**32 - 1) ^ variant_seed)

    if family == "bar":
        count = 6 if variant in {"category", "atlas"} else 4
        groups = 3 if variant not in {"composition", "beforeafter"} else 2
        x = np.arange(count)
        values = np.clip(local.normal(0.58, 0.18, (groups, count)), 0.12, 0.96)
        if variant == "composition":
            values = values / values.sum(axis=0)
            ax.bar(x, values[0], color=colors[0], width=0.72)
            ax.bar(x, values[1], bottom=values[0], color=colors[2], width=0.72)
            ax.set_ylim(0, 1)
        else:
            width = 0.72 / groups
            for group in range(groups):
                ax.bar(x + (group - (groups - 1) / 2) * width, values[group], width * 0.92, color=colors[group], edgecolor="white", lw=0.3)
                if variant in {"ablation", "beforeafter"}:
                    raw = values[group] + local.normal(0, 0.035, (5, count))
                    ax.scatter(np.repeat(x + (group - (groups - 1) / 2) * width, 5) + local.normal(0, width * 0.12, count * 5), raw.T.ravel(), s=3.5, color="#34414b", alpha=0.45, zorder=4, linewidth=0)
            ax.set_ylim(0, 1.06)
        ax.set_xticks(x, [f"{i + 1}" for i in x], fontsize=5)
        _clean_axis(ax)
    elif family == "line":
        x = np.linspace(0, 1, 12)
        groups = 2 if variant in {"calibration", "monthly"} else 3
        for group in range(groups):
            slope = (0.33 if group % 2 == 0 else -0.16) + local.normal(0, 0.08)
            y = 0.28 + group * 0.12 + slope * x + np.cumsum(local.normal(0, 0.018, len(x)))
            err = 0.025 + local.random(len(x)) * 0.02
            ax.plot(x, y, color=colors[group], lw=1.15, marker=("o", "s", "^")[group], ms=2.0)
            if variant not in {"sweep", "forecast"}:
                ax.fill_between(x, y - err, y + err, color=colors[group], alpha=0.12, linewidth=0)
        if variant == "calibration":
            ax.plot([0, 1], [0, 1], color="#606d77", ls="--", lw=0.7)
        _clean_axis(ax)
    elif family == "heatmap":
        rows, columns = (10, 10) if variant in {"matrix", "atlas"} else (8, 11)
        matrix = local.normal(0, 0.75, (rows, columns))
        matrix += np.linspace(-0.7, 0.7, rows)[:, None]
        cmap = "RdBu_r" if variant not in {"response", "optimization"} else "magma"
        ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=-2.2 if cmap == "RdBu_r" else None, vmax=2.2 if cmap == "RdBu_r" else None)
        ax.set_xticks([]); ax.set_yticks([])
        if variant in {"markers", "composition"}:
            for edge in np.linspace(0.5, columns - 0.5, 4):
                ax.axvline(edge, color="white", lw=0.45, alpha=0.7)
    elif family == "scatter":
        clusters = 4 if variant in {"embedding", "umap", "trajectory"} else 3
        for group in range(clusters):
            center = np.array([np.cos(group * 1.9), np.sin(group * 1.9)]) * (1.1 if variant != "paired" else 0.65)
            points = local.normal(center, [0.28, 0.22], (45 if variant != "spots" else 80, 2))
            if variant == "paired":
                before = points[:18]
                after = before + local.normal([0.4, 0.15], [0.12, 0.10], before.shape)
                ax.plot(np.c_[before[:, 0], after[:, 0]].T, np.c_[before[:, 1], after[:, 1]].T, color="#aeb7bd", lw=0.35, zorder=0)
                ax.scatter(before[:, 0], before[:, 1], s=7, color=colors[0], alpha=0.65)
                ax.scatter(after[:, 0], after[:, 1], s=7, color=colors[2], alpha=0.65)
                break
            sizes = local.uniform(6, 30, len(points)) if variant in {"groups", "spots", "atlas"} else 8
            ax.scatter(points[:, 0], points[:, 1], s=sizes, color=colors[group % len(colors)], alpha=0.64, linewidth=0.2, edgecolor="white")
        if variant == "trajectory":
            path = np.cumsum(local.normal(0, 0.18, (12, 2)), axis=0)
            ax.plot(path[:, 0], path[:, 1], color="#3e4a53", lw=1.0, marker="o", ms=2)
        _clean_axis(ax, grid=False)
    elif family == "distribution":
        if variant in {"hist", "atlas"}:
            for group in range(3):
                data = local.normal(group * 0.45, 0.55, 180)
                ax.hist(data, bins=15, density=True, histtype="stepfilled", alpha=0.26, color=colors[group])
        elif variant == "ridge":
            for row in range(5):
                data = local.normal(0.2 * row, 0.5, 130)
                counts, edges = np.histogram(data, bins=25, density=True)
                centers = (edges[:-1] + edges[1:]) / 2
                ax.fill_between(centers, row, row + counts * 0.34, color=colors[row % len(colors)], alpha=0.72)
        else:
            samples = [local.normal(group * 0.22, 0.45, 55) for group in range(4)]
            violin = ax.violinplot(samples, showmedians=True, widths=0.78)
            for body, color in zip(violin["bodies"], colors):
                body.set_facecolor(color); body.set_edgecolor("white"); body.set_alpha(0.65)
            if variant == "points":
                for x, data in enumerate(samples, start=1):
                    ax.scatter(local.normal(x, 0.055, len(data)), data, s=3, color="#3e4a53", alpha=0.35, linewidth=0)
        _clean_axis(ax, grid=False)
    elif family == "forest":
        y = np.arange(7)
        effect = local.normal(0.1, 0.28, len(y))
        errors = local.uniform(0.1, 0.28, len(y))
        ax.errorbar(effect, y, xerr=errors, fmt="o", ms=3, color=colors[index % len(colors)], ecolor="#74808a", capsize=1.5)
        ax.axvline(0, color="#4f5b64", lw=0.65, ls="--")
        ax.set_yticks(y, [f"{i + 1}" for i in y], fontsize=5)
        _clean_axis(ax, grid=False)
    elif family == "area":
        x = np.arange(15)
        raw = local.gamma(2, 1, (4, len(x)))
        values = raw / raw.sum(axis=0)
        ax.stackplot(x, values, colors=colors[:4], alpha=0.85, linewidth=0.25, edgecolor="white")
        ax.set_ylim(0, 1); _clean_axis(ax, grid=False)
    elif family == "spatial":
        field = _synthetic_field(local, 100)
        cmap = {"sample": "magma", "mask": "gray", "overlay": "viridis", "zoom": "cividis"}.get(variant, "magma")
        ax.imshow(field, cmap=cmap)
        if variant in {"overlay", "spots", "atlas"}:
            spots = local.uniform(4, 96, (35, 2))
            ax.scatter(spots[:, 0], spots[:, 1], s=5, facecolors="none", edgecolors="white", lw=0.35)
        ax.plot([6, 28], [93, 93], color="white", lw=1.5)
        ax.set_axis_off()
    elif family == "network":
        nodes = np.c_[np.cos(np.linspace(0, 2 * np.pi, 10, endpoint=False)), np.sin(np.linspace(0, 2 * np.pi, 10, endpoint=False))]
        for _ in range(16):
            source, target = local.choice(len(nodes), 2, replace=False)
            ax.plot(nodes[[source, target], 0], nodes[[source, target], 1], color="#adb8bf", lw=0.4, zorder=0)
        ax.scatter(nodes[:, 0], nodes[:, 1], s=31, c=[colors[i % 4] for i in range(len(nodes))], edgecolor="white", lw=0.45)
        ax.set_aspect("equal"); ax.set_axis_off()
    elif family == "manifold":
        t = 1.5 * np.pi * (1 + 2 * local.random(260))
        x, y = t * np.cos(t), t * np.sin(t)
        noise = 0.3 if variant != "holes" else 0.55
        ax.scatter(x + local.normal(0, noise, len(t)), y + local.normal(0, noise, len(t)), c=t, cmap="viridis", s=3.5, alpha=0.72, linewidth=0)
        ax.set_xticks([]); ax.set_yticks([]); ax.spines[:].set_visible(False)
    elif family == "radar":
        angles = np.linspace(0, 2 * np.pi, 7, endpoint=False)
        for group in range(3):
            values = np.clip(0.45 + 0.12 * group + local.normal(0, 0.08, len(angles)), 0.12, 0.94)
            coords = np.c_[values * np.cos(angles), values * np.sin(angles)]
            coords = np.vstack([coords, coords[0]])
            ax.plot(coords[:, 0], coords[:, 1], color=colors[group], lw=1.0)
            ax.fill(coords[:, 0], coords[:, 1], color=colors[group], alpha=0.08)
        for radius in (0.3, 0.6, 0.9):
            ax.add_patch(plt.Circle((0, 0), radius, fill=False, lw=0.35, ec="#ccd4d9"))
        ax.set_aspect("equal"); ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.1, 1.1); ax.set_axis_off()
    elif family in {"schematic", "diagram"}:
        ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.set_axis_off()
        count = 4 if family == "schematic" else 3
        positions = np.linspace(1.2, 8.8, count)
        for node, x in enumerate(positions):
            if family == "schematic":
                box = FancyBboxPatch((x - 0.82, 2.65), 1.64, 1.0, boxstyle="round,pad=0.08", fc=colors[node % len(colors)], ec="white", lw=0.7, alpha=0.92)
                ax.add_patch(box)
                ax.text(x, 3.15, ("Input", "Encode", "Model", "Readout")[node], ha="center", va="center", color="white", fontsize=5.5, fontweight="bold")
            else:
                ax.add_patch(Circle((x, 3.1), 0.55, fc=colors[node % len(colors)], ec="white", lw=0.7, alpha=0.85))
            if node < count - 1:
                ax.add_patch(FancyArrowPatch((x + 0.84, 3.15), (positions[node + 1] - 0.84, 3.15), arrowstyle="-|>", mutation_scale=8, lw=0.8, color="#59656e"))
        for _ in range(8):
            ax.add_patch(Circle((local.uniform(0.7, 9.3), local.uniform(0.8, 1.9)), local.uniform(0.07, 0.16), fc=colors[local.integers(0, len(colors))], ec="white", lw=0.25, alpha=0.66))
    elif family == "table":
        rows, columns = 5, 4
        matrix = local.uniform(0.25, 0.95, (rows, columns))
        ax.imshow(matrix, cmap="Blues", aspect="auto", vmin=0, vmax=1)
        for y in np.arange(-0.5, rows, 1): ax.axhline(y, color="white", lw=0.55)
        for x in np.arange(-0.5, columns, 1): ax.axvline(x, color="white", lw=0.55)
        ax.set_xticks([]); ax.set_yticks([])
    elif family == "survival":
        x = np.linspace(0, 1, 12)
        for group in range(3):
            y = np.maximum(0, 1 - (0.35 + group * 0.15) * x - np.cumsum(local.uniform(0, 0.03, len(x))))
            ax.step(x, y, where="post", color=colors[group], lw=1.15)
        ax.set_ylim(0, 1.05); _clean_axis(ax, grid=False)
    else:
        raise ValueError(f"Unsupported source-specific panel kind: {kind}")


def _render_blueprint(fig: plt.Figure, rng: np.random.Generator, colors: tuple[str, ...], blueprint: dict[str, Any]) -> None:
    mosaic = [list(row) for row in blueprint["mosaic"]]
    axes = fig.subplot_mosaic(mosaic, empty_sentinel=".")
    recipes = {item["id"]: item["kind"] for item in blueprint["panel_recipes"]}
    for index, (slot, ax) in enumerate(axes.items()):
        _draw_panel_kind(ax, recipes[slot], rng, colors, index)
        _panel_label(ax, slot)
    fig.text(0.99, 0.006, blueprint["blueprint_id"].replace("_", " "), ha="right", va="bottom", fontsize=4.5, color="#7b8790")


RENDERERS: dict[str, Callable[[plt.Figure, np.random.Generator, tuple[str, ...]], None]] = {
    "grouped_bar": _grouped_bar,
    "line_grid": _line_grid,
    "heatmap_grid": _heatmap_grid,
    "scatter_bubble": _scatter_bubble,
    "radar_grid": _radar_grid,
    "distribution_grid": _distribution_grid,
    "forest_interval": _forest_interval,
    "area_stacked": _area_stacked,
    "spatial_image_plate": _spatial_image_plate,
    "network_matrix": _network_matrix,
    "manifold_3d": _manifold_3d,
    "mechanism_schematic": _mechanism_schematic,
    "comparison_composite": _comparison_composite,
}


def render_from_spec(spec: dict[str, Any], output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    seed = int(spec["source_fingerprint"][:16], 16) % (2**32)
    rng, colors = _style(seed)
    aspect = max(0.7, min(2.2, float(spec["width"]) / float(spec["height"])))
    width = 7.2 if aspect >= 1 else 6.2
    height = max(4.2, min(7.0, width / aspect))
    blueprint = spec.get("reconstruction_blueprint")
    if not blueprint:
        raise ValueError("A source reconstruction requires a source-specific reconstruction_blueprint.")
    panel_count = len(blueprint.get("panel_recipes", []))
    if panel_count >= 8:
        width = max(width, 8.5)
        height = max(height, 6.2)
    with plt.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7,
            "axes.linewidth": 0.6,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    ):
        fig = plt.figure(figsize=(width, height), dpi=150, constrained_layout=True)
        _render_blueprint(fig, rng, colors, blueprint)
        fig.savefig(output_path, dpi=150, bbox_inches="tight", pad_inches=0.08, metadata={"Software": "publication-figure-design"})
        plt.close(fig)
    return output_path


def render_reconstruction(record: SourceFigure, output_path: Path | str) -> Path:
    spec = {
        "source_fingerprint": record.source_sha256,
        "width": record.width,
        "height": record.height,
        "visual_family": record.visual_family,
        "observable_visual_grammar": visual_profile(record),
        "reconstruction_blueprint": reconstruction_blueprint(record),
        "renderer_version": RENDERER_VERSION,
    }
    return render_from_spec(spec, output_path)


def _existing_source_copies(skill_root: Path, records: Iterable[SourceFigure]) -> dict[str, str]:
    by_hash = {record.source_sha256 for record in records}
    matches: dict[str, str] = {}
    refs = skill_root / "assets/visual-references/references"
    if not refs.is_dir():
        return matches
    for metadata_path in refs.glob("*/metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        digest = metadata.get("sha256")
        if digest in by_hash:
            matches[digest] = str(metadata.get("id", metadata_path.parent.name))
    return matches


def _reproducer_text(spec: dict[str, Any]) -> str:
    return (
        "#!/usr/bin/env python3\n"
        '"""Reproduce this independently generated visual-grammar example."""\n\n'
        "import sys\n"
        "import importlib.util\n"
        "from pathlib import Path\n"
        "SKILL_ROOT = Path(__file__).resolve().parents[4]\n"
        "MODULE_PATH = SKILL_ROOT / 'scripts' / 'source_reconstruction_library.py'\n"
        "sys.path.insert(0, str(MODULE_PATH.parent))\n"
        "module_spec = importlib.util.spec_from_file_location('source_reconstruction_library', MODULE_PATH)\n"
        "module = importlib.util.module_from_spec(module_spec)\n"
        "sys.modules[module_spec.name] = module\n"
        "module_spec.loader.exec_module(module)\n"
        "render_from_spec = module.render_from_spec\n\n"
        f"SPEC = {repr(spec)}\n\n"
        "if __name__ == '__main__':\n"
        "    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))\n"
    )


def build_reconstruction_library(
    nature_root: Path | str,
    figures_root: Path | str,
    skill_root: Path | str,
) -> dict[str, Any]:
    skill_root = Path(skill_root)
    records = discover_sources(nature_root, figures_root)
    manifest_path = skill_root / MANIFEST_RELATIVE_PATH
    existing_records: dict[str, dict[str, Any]] = {}
    if manifest_path.is_file():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        existing_records = {item["source_fingerprint"]: item for item in current.get("records", [])}

    lib = ReferenceLibrary(root=skill_root, registry_path=skill_root / "assets/registry.jsonl")
    existing_copies = _existing_source_copies(skill_root, records)
    output_records: list[dict[str, Any]] = []
    created = 0

    with tempfile.TemporaryDirectory(prefix="afs_source_reconstruction_") as tmp_name:
        tmp = Path(tmp_name)
        for index, record in enumerate(records, start=1):
            previous = existing_records.get(record.source_sha256)
            if previous and previous.get("renderer_version") == RENDERER_VERSION:
                image = skill_root / previous.get("image_path", "")
                metadata = skill_root / "assets/visual-references/generated-archive" / previous.get("archive_id", "") / "metadata.json"
                if image.is_file() and metadata.is_file():
                    current_spec = {
                        "source_fingerprint": record.source_sha256,
                        "width": record.width,
                        "height": record.height,
                        "visual_family": record.visual_family,
                        "observable_visual_grammar": visual_profile(record),
                        "reconstruction_blueprint": reconstruction_blueprint(record),
                        "renderer_version": RENDERER_VERSION,
                    }
                    code = skill_root / previous.get("code_path", "")
                    if code.parent == metadata.parent:
                        code.write_text(_reproducer_text(current_spec), encoding="utf-8")
                    refreshed = dict(previous)
                    refreshed["renderer_version"] = RENDERER_VERSION
                    refreshed["reconstruction_blueprint"] = reconstruction_blueprint(record)
                    output_records.append(refreshed)
                    continue

            image_path = tmp / f"reconstruction-{index:02d}.png"
            code_path = tmp / f"reconstruction-{index:02d}.py"
            render_reconstruction(record, image_path)
            spec = {
                "source_fingerprint": record.source_sha256,
                "width": record.width,
                "height": record.height,
                "visual_family": record.visual_family,
                "observable_visual_grammar": visual_profile(record),
                "reconstruction_blueprint": reconstruction_blueprint(record),
                "renderer_version": RENDERER_VERSION,
            }
            code_path.write_text(_reproducer_text(spec), encoding="utf-8")
            metadata_override = {
                "subtype": record.visual_family,
                "tags": ["source-reconstruction", record.repository, record.visual_family],
                "layout": "multi-panel" if record.visual_family not in {"mechanism_schematic"} else "schematic",
                "source": "independent visual-grammar reconstruction",
                "source_url": None,
                "license": "generated independently; source license recorded in audit manifest",
                "usage_scope": "internal_reference",
                "review_status": "pending",
                "aesthetic_rating": None,
                "production_ready": False,
                "notes": "Synthetic data and independent code; source pixels and plotting code were not copied.",
                "source_fingerprint": record.source_sha256,
                "source_repository": record.repository,
                "source_relative_path": record.relative_path,
                "source_license_class": record.license_class,
                "source_action": record.source_action,
                "visual_family": record.visual_family,
                "reconstruction_method": "independent",
                "observable_visual_grammar": visual_profile(record),
                "reconstruction_blueprint": reconstruction_blueprint(record),
                "renderer_version": RENDERER_VERSION,
            }
            generated_sha = _sha256(image_path)
            existing_ref = lib.get(generated_sha[:16])
            if existing_ref is not None and existing_ref.scope == "generated-archive":
                asset_dir = skill_root / "assets/visual-references/generated-archive" / existing_ref.id
                archived_code = asset_dir / "code.py"
                shutil.copy2(code_path, archived_code)
                existing_ref.metadata.update(metadata_override)
                existing_ref.metadata["code_path"] = archived_code.relative_to(skill_root).as_posix()
                (asset_dir / "metadata.json").write_text(
                    json.dumps(existing_ref.metadata, indent=2, ensure_ascii=False, sort_keys=True),
                    encoding="utf-8",
                )
                ref = existing_ref
            else:
                ref = lib.archive_generated_figure(
                    image_path,
                    figure_type=record.visual_family,
                    code_path=code_path,
                    metadata_override=metadata_override,
                )
            if previous and previous.get("archive_id") != ref.id:
                previous_dir = skill_root / "assets/visual-references/generated-archive" / str(previous["archive_id"])
                generated_root = (skill_root / "assets/visual-references/generated-archive").resolve()
                if previous_dir.resolve().parent == generated_root and previous_dir.is_dir():
                    shutil.rmtree(previous_dir)
            item = {
                **record.public_dict(),
                "source_fingerprint": record.source_sha256,
                "archive_id": ref.id,
                "scope": ref.scope,
                "image_path": ref.metadata["image_path"],
                "code_path": ref.metadata.get("code_path"),
                "output_sha256": ref.metadata["sha256"],
                "reconstruction_method": "independent",
                "renderer_version": RENDERER_VERSION,
                "reconstruction_blueprint": reconstruction_blueprint(record),
                "existing_exact_copy_id": existing_copies.get(record.source_sha256),
            }
            item.pop("source_sha256", None)
            output_records.append(item)
            created += 1

    output_records.sort(key=lambda item: (item["repository"], item["relative_path"].lower()))
    repository_counts = {
        name: sum(item["repository"] == name for item in output_records)
        for name in ("nature-figure", "figures4papers")
    }
    manifest = {
        "schema_version": 1,
        "policy": {
            "source_pixels_copied": False,
            "source_code_copied": False,
            "unknown_license_action": "independent_reconstruction",
        },
        "summary": {
            "source_count": len(output_records),
            "created_count": created,
            "nature_figure_count": repository_counts["nature-figure"],
            "figures4papers_count": repository_counts["figures4papers"],
            "existing_exact_copy_count": sum(bool(item.get("existing_exact_copy_id")) for item in output_records),
        },
        "records": output_records,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lib.rebuild_registry()
    return manifest


def validate_installed_library(
    skill_root: Path | str,
    expected_counts: dict[str, int] | None = EXPECTED_COUNTS,
) -> dict[str, Any]:
    skill_root = Path(skill_root)
    errors: list[str] = []
    manifest_path = skill_root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        return {"ok": False, "errors": [f"Missing {MANIFEST_RELATIVE_PATH.as_posix()}"], "metrics": {}}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "errors": [f"Invalid reconstruction manifest: {exc}"], "metrics": {}}
    records = manifest.get("records", [])
    fingerprints = [item.get("source_fingerprint") for item in records]
    archive_ids = [item.get("archive_id") for item in records]
    if len(fingerprints) != len(set(fingerprints)):
        errors.append("Source fingerprints are not one-to-one.")
    if len(archive_ids) != len(set(archive_ids)):
        errors.append("Archive IDs are not one-to-one.")
    if expected_counts:
        actual = {
            "nature-figure": sum(item.get("repository") == "nature-figure" for item in records),
            "figures4papers": sum(item.get("repository") == "figures4papers" for item in records),
            "total": len(records),
        }
        for key, expected in expected_counts.items():
            if actual.get(key) != expected:
                errors.append(f"Expected {expected} {key} records; found {actual.get(key)}.")
    for item in records:
        label = item.get("source_fingerprint", "unknown")[:12]
        if item.get("scope") != "generated-archive":
            errors.append(f"{label}: scope is not generated-archive.")
        if item.get("reconstruction_method") != "independent":
            errors.append(f"{label}: reconstruction method is not independent.")
        if item.get("source_fingerprint") == item.get("output_sha256"):
            errors.append(f"{label}: output is byte-identical to source.")
        blueprint = item.get("reconstruction_blueprint")
        if not isinstance(blueprint, dict) or not blueprint.get("blueprint_id"):
            errors.append(f"{label}: missing source-specific reconstruction blueprint.")
        elif not isinstance(blueprint.get("panel_recipes"), list) or not blueprint["panel_recipes"]:
            errors.append(f"{label}: blueprint has no panel recipes.")
        for field in ("relative_path", "image_path", "code_path"):
            value = item.get(field)
            if not value or Path(value).is_absolute():
                errors.append(f"{label}: {field} is missing or absolute.")
        image_path = skill_root / item.get("image_path", "")
        code_path = skill_root / item.get("code_path", "")
        metadata_path = skill_root / "assets/visual-references/generated-archive" / str(item.get("archive_id", "")) / "metadata.json"
        for path in (image_path, code_path, metadata_path):
            if not path.is_file():
                errors.append(f"{label}: missing archive file {path.relative_to(skill_root).as_posix()}.")
        if image_path.is_file():
            try:
                with Image.open(image_path) as image:
                    image.verify()
            except Exception as exc:  # pragma: no cover - checker reports third-party decoder failures
                errors.append(f"{label}: invalid image: {exc}")
            if _sha256(image_path) != item.get("output_sha256"):
                errors.append(f"{label}: output SHA does not match image bytes.")
        if code_path.is_file():
            code = code_path.read_text(encoding="utf-8", errors="replace").lower()
            if "figures4papers" in code or "nature-skills" in code:
                errors.append(f"{label}: archived code names a source repository.")
        if metadata_path.is_file():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            review = metadata.get("visual_review")
            if review is None:
                if metadata.get("review_status") != "pending":
                    errors.append(f"{label}: unreviewed reconstruction is not pending.")
                if metadata.get("aesthetic_rating") is not None:
                    errors.append(f"{label}: unreviewed reconstruction has an aesthetic rating.")
            else:
                required_review = {
                    "final_size_inspected", "hierarchy", "panel_balance", "whitespace",
                    "legend_footprint", "text_legibility", "reviewer", "verdict", "comparison_path",
                }
                missing = sorted(field for field in required_review if not review.get(field))
                if missing:
                    errors.append(f"{label}: incomplete visual review: {', '.join(missing)}.")
                comparison = skill_root / str(review.get("comparison_path", ""))
                if not comparison.is_file():
                    errors.append(f"{label}: missing visual review comparison evidence.")
                if review.get("verdict") == "pass":
                    if metadata.get("review_status") != "reviewed" or metadata.get("aesthetic_rating") is None:
                        errors.append(f"{label}: passing review is not retrievable with a rating.")
                elif review.get("verdict") == "fail":
                    if metadata.get("review_status") != "pending" or metadata.get("aesthetic_rating") is not None:
                        errors.append(f"{label}: failed review is not quarantined.")
                else:
                    errors.append(f"{label}: visual review verdict is invalid.")
            if metadata.get("production_ready") is not False:
                errors.append(f"{label}: automated reconstruction is marked production-ready.")
    lib = ReferenceLibrary(root=skill_root, registry_path=skill_root / "assets/registry.jsonl")
    ok, problems = lib.validate()
    if not ok:
        errors.extend(f"Reference {ref_id}: {'; '.join(problem)}" for ref_id, problem in problems)
    return {
        "ok": not errors,
        "errors": errors,
        "metrics": {
            "records": len(records),
            "visual_families": len({item.get("visual_family") for item in records}),
            "existing_exact_copies": sum(bool(item.get("existing_exact_copy_id")) for item in records),
        },
    }


def quarantine_installed_reconstructions(skill_root: Path | str) -> dict[str, Any]:
    """Reset automated source reconstructions to an honest unreviewed state."""
    skill_root = Path(skill_root)
    manifest_path = skill_root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    changed = 0
    for item in manifest.get("records", []):
        meta_path = (
            skill_root / "assets/visual-references/generated-archive"
            / str(item.get("archive_id", "")) / "metadata.json"
        )
        if not meta_path.is_file():
            continue
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        target = {"review_status": "pending", "aesthetic_rating": None, "production_ready": False}
        if any(metadata.get(key) != value for key, value in target.items()):
            metadata.update(target)
            note = "Automated reconstruction; quarantined pending source-to-render visual review."
            existing_note = str(metadata.get("notes") or "").strip()
            if note not in existing_note:
                metadata["notes"] = f"{existing_note} {note}".strip()
            meta_path.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            changed += 1
    ReferenceLibrary(
        root=skill_root, registry_path=skill_root / "assets/registry.jsonl"
    ).rebuild_registry()
    return {"changed_count": changed, "record_count": len(manifest.get("records", []))}


def write_visual_review(
    skill_root: Path | str,
    source_fingerprint: str,
    verdict: str,
    reviewer: str,
    notes: str,
    comparison_path: Path | str,
    rating: float | None = None,
) -> dict[str, Any]:
    """Record a manual equal-size source-to-render review without auto-promotion."""
    if verdict not in {"pass", "fail"}:
        raise ValueError("verdict must be 'pass' or 'fail'")
    skill_root = Path(skill_root)
    manifest_path = skill_root / MANIFEST_RELATIVE_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    item = next(
        (entry for entry in manifest.get("records", []) if entry.get("source_fingerprint") == source_fingerprint),
        None,
    )
    if item is None:
        raise KeyError(f"Unknown source fingerprint: {source_fingerprint}")
    comparison = Path(comparison_path)
    if not comparison.is_file():
        raise FileNotFoundError(f"Missing comparison evidence: {comparison}")
    try:
        relative_comparison = comparison.resolve().relative_to(skill_root.resolve()).as_posix()
    except ValueError:
        evidence_dir = skill_root / "assets/visual-references/review-evidence" / str(item["archive_id"])
        evidence_dir.mkdir(parents=True, exist_ok=True)
        destination = evidence_dir / comparison.name
        shutil.copy2(comparison, destination)
        relative_comparison = destination.relative_to(skill_root).as_posix()
    review = {
        "reviewer": reviewer,
        "verdict": verdict,
        "reviewed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "comparison_path": relative_comparison,
        "final_size_inspected": True,
        "hierarchy": "pass" if verdict == "pass" else "fail",
        "panel_balance": "pass" if verdict == "pass" else "fail",
        "whitespace": "pass" if verdict == "pass" else "fail",
        "legend_footprint": "pass" if verdict == "pass" else "fail",
        "text_legibility": "pass" if verdict == "pass" else "fail",
        "notes": notes,
    }
    item["visual_review"] = review
    metadata_path = skill_root / "assets/visual-references/generated-archive" / item["archive_id"] / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["visual_review"] = review
    if verdict == "pass":
        if rating is None or not 0 <= rating <= 5:
            raise ValueError("A passing review requires a rating from 0 to 5")
        metadata.update({"review_status": "reviewed", "aesthetic_rating": rating, "production_ready": False})
    else:
        metadata.update({"review_status": "pending", "aesthetic_rating": None, "production_ready": False})
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    ReferenceLibrary(root=skill_root, registry_path=skill_root / "assets/registry.jsonl").rebuild_registry()
    return review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="Build or update the reconstruction library.")
    build.add_argument("--nature-root", required=True, type=Path)
    build.add_argument("--figures-root", required=True, type=Path)
    build.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    check = subparsers.add_parser("check", help="Validate the installed reconstruction library.")
    check.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    check.add_argument("--json", action="store_true")
    quarantine = subparsers.add_parser(
        "quarantine", help="Reset automated reconstructions to pending/unrated."
    )
    quarantine.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    review = subparsers.add_parser("review", help="Record one manual source-to-render visual review.")
    review.add_argument("--fingerprint", required=True)
    review.add_argument("--verdict", required=True, choices=("pass", "fail"))
    review.add_argument("--reviewer", required=True)
    review.add_argument("--notes", required=True)
    review.add_argument("--comparison", required=True, type=Path)
    review.add_argument("--rating", type=float)
    review.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    if args.command == "build":
        report = build_reconstruction_library(args.nature_root, args.figures_root, args.skill_root)
        print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
        return 0
    if args.command == "quarantine":
        report = quarantine_installed_reconstructions(args.skill_root)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    if args.command == "review":
        report = write_visual_review(
            args.skill_root, args.fingerprint, args.verdict, args.reviewer,
            args.notes, args.comparison, args.rating,
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    report = validate_installed_library(args.skill_root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Source reconstruction library: {'PASS' if report['ok'] else 'FAIL'}")
        for error in report["errors"]:
            print(f"  ERROR: {error}")
        for key, value in report.get("metrics", {}).items():
            print(f"  {key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
