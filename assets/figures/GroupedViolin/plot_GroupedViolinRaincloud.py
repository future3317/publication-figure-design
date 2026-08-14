# -*- coding: utf-8 -*-
"""Grouped violin + box + jitter raincloud plot with significance brackets.

Reproduces the WeChat reference style:
  * half-violin on each side
  * white boxplot in the middle
  * jittered individual points
  * pairwise significance brackets above the violins
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
from scipy import stats

try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from palette_manager import get_palette
except Exception:  # pragma: no cover
    def get_palette(name: str, n: Optional[int] = None) -> List[str]:
        fallback = ["#377EB8", "#E41A1C", "#4DAF4A", "#984EA3", "#FF7F00",
                    "#FFFF33", "#A65628", "#F781BF"]
        if n is None:
            return fallback
        return [fallback[i % len(fallback)] for i in range(n)]


def _configure_fonts() -> None:
    preferred = ["Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS"]
    available = {f.name for f in plt.matplotlib.font_manager.fontManager.ttflist}
    chosen = next((f for f in preferred if f in available), None)
    if chosen:
        plt.rcParams["font.family"] = [chosen, "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


_configure_fonts()


def _half_violin(
    ax,
    data: Sequence[np.ndarray],
    positions: Sequence[float],
    colors: Sequence[str],
    side: str = "left",
    width: float = 0.55,
    alpha: float = 0.45,
    zorder: int = 1,
):
    for pos, vals, color in zip(positions, data, colors):
        vals = np.asarray(vals)
        kde = stats.gaussian_kde(vals)
        y_grid = np.linspace(vals.min(), vals.max(), 200)
        density = kde(y_grid)
        density = density / density.max() * (width / 2)
        x_fill = pos - density if side == "left" else pos + density
        ax.fill_betweenx(
            y_grid, pos, x_fill,
            color=color, alpha=alpha, edgecolor="black", linewidth=0.5, zorder=zorder,
        )
        ax.plot([pos, pos], [vals.min(), vals.max()], color="black", lw=0.5, zorder=zorder)


def _boxplot(ax, data, positions, colors, widths=0.16, zorder=2):
    for pos, vals, color in zip(positions, data, colors):
        vals = np.asarray(vals)
        q1, med, q3 = np.percentile(vals, [25, 50, 75])
        iqr = q3 - q1
        lower = max(vals.min(), q1 - 1.5 * iqr)
        upper = min(vals.max(), q3 + 1.5 * iqr)
        rect = Rectangle((pos - widths / 2, q1), widths, q3 - q1,
                         facecolor="white", edgecolor=color, linewidth=1.2, zorder=zorder)
        ax.add_patch(rect)
        ax.plot([pos - widths / 2, pos + widths / 2], [med, med], color="black", lw=1.3, zorder=zorder + 1)
        ax.plot([pos, pos], [lower, q1], color="black", lw=0.8, zorder=zorder)
        ax.plot([pos, pos], [q3, upper], color="black", lw=0.8, zorder=zorder)
        ax.plot([pos - widths / 4, pos + widths / 4], [lower, lower], color="black", lw=0.8, zorder=zorder)
        ax.plot([pos - widths / 4, pos + widths / 4], [upper, upper], color="black", lw=0.8, zorder=zorder)


def _p_star_text(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def plot_grouped_violin_raincloud(
    df: pd.DataFrame,
    value_col: str = "value",
    group_col: str = "group",
    groups_order: Optional[Sequence[str]] = None,
    palette: Optional[Sequence[str]] = None,
    markers: Optional[Sequence[str]] = None,
    compare_pairs: Optional[Sequence[Tuple[str, str]]] = None,
    figsize: Tuple[float, float] = (6.5, 5),
    ylabel: Optional[str] = None,
    xlabel: Optional[str] = None,
    p_text_size: float = 9,
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    if groups_order is None:
        groups_order = sorted(df[group_col].unique())
    groups_order = list(groups_order)

    palette = palette or get_palette("summer_beach", n=len(groups_order))
    markers = markers or ["o", "s", "^", "D", "v", "p", "h", "X"][:len(groups_order)]

    data_by_group = [df[df[group_col] == g][value_col].dropna().to_numpy() for g in groups_order]
    positions = np.arange(1, len(groups_order) + 1)

    fig, ax = plt.subplots(figsize=figsize)

    # Violins on both sides for symmetry.
    _half_violin(ax, data_by_group, positions, palette, side="left", width=0.6, alpha=0.4)
    _half_violin(ax, data_by_group, positions, palette, side="right", width=0.6, alpha=0.4)

    # Box in the middle.
    _boxplot(ax, data_by_group, positions, palette, widths=0.18)

    # Jittered points.
    rng = np.random.default_rng(42)
    for pos, vals, color, marker in zip(positions, data_by_group, palette, markers):
        x_jitter = pos + rng.normal(0, 0.05, len(vals))
        ax.scatter(x_jitter, vals, color=color, marker=marker, s=22,
                   edgecolor="white", linewidth=0.3, alpha=0.65, zorder=3)

    ax.set_xlim(0.4, len(groups_order) + 0.6)
    ax.set_xticks(positions)
    ax.set_xticklabels(groups_order, fontsize=10)
    ax.set_xlabel(xlabel or group_col, fontsize=11)
    ax.set_ylabel(ylabel or value_col, fontsize=11)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    # Pairwise significance brackets.
    if compare_pairs is None:
        compare_pairs = [(groups_order[i], groups_order[i + 1])
                         for i in range(len(groups_order) - 1)]

    y_top = max(y.max() for y in data_by_group)
    y_lo, y_hi = ax.get_ylim()
    y_range = y_hi - y_lo
    bracket_y = y_top + 0.04 * y_range
    bracket_step = 0.05 * y_range

    for i, (a, b) in enumerate(compare_pairs):
        if a not in groups_order or b not in groups_order:
            continue
        idx_a, idx_b = groups_order.index(a), groups_order.index(b)
        ya, yb = data_by_group[idx_a], data_by_group[idx_b]
        _, pval = stats.ttest_ind(ya, yb, equal_var=False)
        x1, x2 = positions[idx_a], positions[idx_b]
        y_line = bracket_y + i * bracket_step
        tick = bracket_step * 0.15
        ax.plot([x1, x1, x2, x2], [y_line - tick, y_line, y_line, y_line - tick],
                color="black", lw=0.9)
        ax.text((x1 + x2) / 2, y_line + tick * 0.3, _p_star_text(pval),
                ha="center", va="bottom", fontsize=p_text_size)

    ax.set_ylim(y_lo, bracket_y + len(compare_pairs) * bracket_step + 0.06 * y_range)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig, ax


def make_demo_data(seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    groups = ["CR", "PF", "G3", "组4", "G5"]
    centers = [10.5, 17.5, 14.0, 16.0, 12.0]
    scales = [2.5, 3.0, 2.2, 2.8, 2.4]
    records = []
    for g, c, s in zip(groups, centers, scales):
        values = rng.normal(c, s, 60)
        for v in values:
            records.append({"group": g, "value": v})
    return pd.DataFrame(records)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Grouped violin + box + raincloud plot")
    parser.add_argument("--data", type=str, default=None, help="CSV with columns value,group")
    parser.add_argument("--output", type=str, default="GroupedViolinRaincloud.png")
    parser.add_argument("--palette", type=str, default=None)
    args = parser.parse_args(argv)

    if args.data:
        df = pd.read_csv(args.data, encoding="utf-8-sig")
    else:
        df = make_demo_data()

    palette = None
    if args.palette:
        palette = [c.strip() for c in args.palette.split(",")] if "," in args.palette else get_palette(args.palette, n=df["group"].nunique())

    groups_order = ["CR", "PF", "G3", "组4", "G5"] if not args.data else None
    plot_grouped_violin_raincloud(
        df,
        value_col="value",
        group_col="group",
        groups_order=groups_order,
        ylabel="Values",
        xlabel="Groups",
        palette=palette,
        save_path=args.output,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
