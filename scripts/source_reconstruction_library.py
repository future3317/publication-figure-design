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
RENDERER_VERSION = 2
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
    grammar = spec.get("observable_visual_grammar", {"panel_grid": [1, 2], "panel_count": 2})
    panel_count = int(grammar.get("panel_count", 2))
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
        family = spec["visual_family"]
        if panel_count >= 8:
            _topology_grid(fig, rng, colors, spec)
        elif family in {"material_mechanism", "in_vivo_efficacy", "single_cell_systems", "validation_perturbation"}:
            _rich_composite(fig, rng, colors, family)
        else:
            RENDERERS.get(family, _comparison_composite)(fig, rng, colors)
        fig.savefig(output_path, dpi=150, bbox_inches="tight", pad_inches=0.08, metadata={"Software": "academic-figure-skill"})
        plt.close(fig)
    return output_path


def render_reconstruction(record: SourceFigure, output_path: Path | str) -> Path:
    spec = {
        "source_fingerprint": record.source_sha256,
        "width": record.width,
        "height": record.height,
        "visual_family": record.visual_family,
        "observable_visual_grammar": visual_profile(record),
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
                        "renderer_version": RENDERER_VERSION,
                    }
                    code = skill_root / previous.get("code_path", "")
                    if code.parent == metadata.parent:
                        code.write_text(_reproducer_text(current_spec), encoding="utf-8")
                    output_records.append(previous)
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
                "review_status": "reviewed",
                "aesthetic_rating": 4,
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
    args = parser.parse_args(argv)
    if args.command == "build":
        report = build_reconstruction_library(args.nature_root, args.figures_root, args.skill_root)
        print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
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
