# -*- coding: utf-8 -*-
"""Correlation matrix trio: numeric heatmap + colour heatmap + circle heatmap.

Reproduces the WeChat reference style for one colour scheme row:
  Left  : correlation matrix with numeric labels inside coloured cells
  Middle: smooth colour heatmap (no text)
  Right : circle / bubble correlation matrix where marker size encodes |r|
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from matplotlib import cm
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from palette_manager import get_palette
except Exception:  # pragma: no cover
    def get_palette(name: str, n: Optional[int] = None) -> List[str]:
        return ["#3AB5B3", "#7B6C9F", "#A188BD", "#BBC5DE", "#E7777F",
                "#976793", "#61829D", "#80C66D"]


def _configure_fonts() -> None:
    preferred = ["Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS"]
    available = {f.name for f in plt.matplotlib.font_manager.fontManager.ttflist}
    chosen = next((f for f in preferred if f in available), None)
    if chosen:
        plt.rcParams["font.family"] = [chosen, "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


_configure_fonts()


def _make_cmap_from_hex(hex_colors: Sequence[str], name: str = "custom") -> LinearSegmentedColormap:
    """Build a continuous colormap from a list of hex colours."""
    rgb = [plt.matplotlib.colors.to_rgb(c) for c in hex_colors]
    return LinearSegmentedColormap.from_list(name, rgb)


def _draw_numeric_heatmap(
    ax,
    corr: pd.DataFrame,
    cmap: LinearSegmentedColormap,
    vmin: float = -1,
    vmax: float = 1,
    text_size: float = 7,
):
    """Heatmap with value labels; colour mapped to the correlation value."""
    n = len(corr)
    im = ax.imshow(corr.values, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(corr.columns, fontsize=8)
    ax.set_yticklabels(corr.index, fontsize=8)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            val = corr.iloc[i, j]
            # Choose text colour by luminance of the cell.
            rgba = cmap((val - vmin) / (vmax - vmin))
            lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            text_color = "white" if lum < 0.5 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    color=text_color, fontsize=text_size)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(n - 0.5, -0.5)
    return im


def _draw_color_heatmap(
    ax,
    corr: pd.DataFrame,
    cmap: LinearSegmentedColormap,
    vmin: float = -1,
    vmax: float = 1,
):
    """Smooth colour heatmap without text."""
    n = len(corr)
    im = ax.imshow(corr.values, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(corr.columns, fontsize=8)
    ax.set_yticklabels(corr.index, fontsize=8)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(n - 0.5, -0.5)
    return im


def _draw_circle_heatmap(
    ax,
    corr: pd.DataFrame,
    cmap: LinearSegmentedColormap,
    vmin: float = -1,
    vmax: float = 1,
    max_size: float = 320,
):
    """Circle / bubble correlation matrix."""
    n = len(corr)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(corr.columns, fontsize=8)
    ax.set_yticklabels(corr.index, fontsize=8)

    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            val = corr.iloc[i, j]
            size = max_size * abs(val)
            color = cmap(norm(val))
            ax.scatter(j, i, s=size, c=[color], edgecolors="white", linewidths=0.5, zorder=2)


def plot_correlation_matrix_combo(
    corr: pd.DataFrame,
    color_scheme: Sequence[str] = ("#053061", "#2166AC", "#4393C3", "#92C5DE",
                                    "#F7F7F7", "#F4A582", "#D6604D", "#B2182B", "#67001F"),
    figsize: Tuple[float, float] = (10, 3.3),
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, np.ndarray]:
    """Draw the trio of correlation-matrix visualisations."""
    cmap = _make_cmap_from_hex(color_scheme, name="corr_cmap")
    n = len(corr)

    fig, axes = plt.subplots(1, 3, figsize=figsize,
                             gridspec_kw={"width_ratios": [1, 1, 1.05]})

    im1 = _draw_numeric_heatmap(axes[0], corr, cmap)
    im2 = _draw_color_heatmap(axes[1], corr, cmap)
    _draw_circle_heatmap(axes[2], corr, cmap)

    for ax in axes:
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis="both", length=0)

    # Colourbars for the first two panels.
    cbar1 = fig.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)
    cbar1.set_label("Interaction", rotation=270, labelpad=15, fontsize=9)
    cbar2 = fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)
    cbar2.set_label("Interaction", rotation=270, labelpad=15, fontsize=9)

    # Legend for circle sizes.
    max_size = 320
    legend_ax = fig.add_axes([0.88, 0.25, 0.02, 0.5])
    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(0, 1)
    legend_ax.axis("off")
    for y, size_factor, label in [(0.75, 0.8, "0.8"), (0.5, 0.5, "0.5"), (0.25, 0.2, "0.2")]:
        legend_ax.scatter(0.3, y, s=max_size * size_factor, c="gray", edgecolors="white", linewidths=0.5)
        legend_ax.text(0.6, y, label, va="center", fontsize=8)

    if title:
        fig.suptitle(title, fontsize=12, y=0.98)

    plt.tight_layout(rect=[0, 0, 0.87, 0.95])
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig, axes


def make_demo_corr(labels: Sequence[str], seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(labels)
    # Generate a positive-definite-ish correlation matrix.
    a = rng.uniform(0.3, 0.9, (n, n))
    corr = (a + a.T) / 2
    np.fill_diagonal(corr, 1.0)
    # Clip to a realistic positive range.
    corr = np.clip(corr, 0.05, 0.95)
    np.fill_diagonal(corr, 1.0)
    return pd.DataFrame(corr, index=labels, columns=labels)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Correlation matrix trio heatmap")
    parser.add_argument("--data", type=str, default=None, help="CSV correlation matrix (index + columns)")
    parser.add_argument("--output", type=str, default="CorrelationMatrixCombo.png")
    parser.add_argument("--scheme", type=str, default="teal-coral",
                        help="Preset: teal-coral, blue-amber, indigo-rose, green-purple")
    args = parser.parse_args(argv)

    if args.data:
        corr = pd.read_csv(args.data, index_col=0, encoding="utf-8-sig")
    else:
        corr = make_demo_corr(["Hmax", "p95", "MOCH", "CRR", "FHD", "VCI"])

    schemes = {
        "teal-coral": ["#053061", "#2166AC", "#4393C3", "#92C5DE",
                       "#F7F7F7", "#F4A582", "#D6604D", "#B2182B", "#67001F"],
        "blue-amber": ["#313695", "#4575B4", "#74ADD1", "#ABD9E9",
                       "#FFFFBF", "#FEE090", "#FDAE61", "#F46D43", "#A50026"],
        "indigo-rose": ["#3B0F70", "#54278F", "#756BB1", "#9E9AC8",
                        "#FDE0DD", "#FC9272", "#FB6A4A", "#DE2D26", "#A50F15"],
        "green-purple": ["#1B7837", "#5AAE61", "#A6DBA0", "#D9F0D3",
                         "#F7F7F7", "#E1D5E7", "#C2A5CF", "#9970AB", "#762A83"],
    }
    scheme = schemes.get(args.scheme, schemes["teal-coral"])

    plot_correlation_matrix_combo(
        corr,
        color_scheme=scheme,
        title="Correlation matrix visualisation",
        save_path=args.output,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
