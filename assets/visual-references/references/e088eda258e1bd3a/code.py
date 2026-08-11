# -*- coding: utf-8 -*-
"""Scatter regression with marginal density / histogram / boxplot panels.

Reproduces the WeChat reference style:
  * Top row: True-vs-Predicted scatter with marginal KDE (left) and
    marginal histogram (right), plus ideal fit dashed line.
  * Bottom row: grouped scatter with per-group regression lines and
    marginal boxplots (left) or marginal histograms (right).
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
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
    from palette_manager import get_palette
except Exception:  # pragma: no cover
    def get_palette(name: str, n: Optional[int] = None) -> List[str]:
        fallback = ["#80C66D", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00"]
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


def _boxplot_mini(ax, data: Sequence[np.ndarray], positions: Sequence[float], colors: Sequence[str]):
    for pos, vals, color in zip(positions, data, colors):
        vals = np.asarray(vals)
        q1, med, q3 = np.percentile(vals, [25, 50, 75])
        iqr = q3 - q1
        lower = max(vals.min(), q1 - 1.5 * iqr)
        upper = min(vals.max(), q3 + 1.5 * iqr)
        width = 0.35
        rect = Rectangle((pos - width / 2, q1), width, q3 - q1,
                         facecolor=color, edgecolor="black", linewidth=0.8, alpha=0.8)
        ax.add_patch(rect)
        ax.plot([pos - width / 2, pos + width / 2], [med, med], color="black", lw=1.0)
        ax.plot([pos, pos], [lower, q1], color="black", lw=0.6)
        ax.plot([pos, pos], [q3, upper], color="black", lw=0.6)


def _scatter_marginal_panel(
    fig,
    rect: Sequence[float],
    x: np.ndarray,
    y: np.ndarray,
    groups: Optional[np.ndarray] = None,
    palette: Optional[Sequence[str]] = None,
    marginal: str = "kde",
    show_regression: bool = False,
    label: str = "(a)",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    annotation: Optional[str] = None,
):
    """Add one scatter-with-marginals panel inside figure rectangle [left,bottom,width,height]."""
    left, bottom, width, height = rect
    margin = 0.18
    main_left = left + margin * width
    main_bottom = bottom + margin * height
    main_width = width * (1 - margin)
    main_height = height * (1 - margin)

    ax_main = fig.add_axes([main_left, main_bottom, main_width, main_height])
    ax_top = fig.add_axes([main_left, main_bottom + main_height, main_width, height * margin * 0.85])
    ax_right = fig.add_axes([main_left + main_width, main_bottom, width * margin * 0.85, main_height])

    if groups is None:
        groups = np.zeros(len(x), dtype=int)
    unique_groups = sorted(set(groups))
    palette = palette or get_palette("soft_forest", n=max(len(unique_groups), 2))
    color_map: Dict[int, str] = {g: palette[i % len(palette)] for i, g in enumerate(unique_groups)}

    xlim = (x.min() - (x.max() - x.min()) * 0.05, x.max() + (x.max() - x.min()) * 0.05)
    ylim = (y.min() - (y.max() - y.min()) * 0.05, y.max() + (y.max() - y.min()) * 0.05)
    ax_main.set_xlim(xlim)
    ax_main.set_ylim(ylim)

    for i, g in enumerate(unique_groups):
        mask = groups == g
        xg, yg = x[mask], y[mask]
        color = color_map[g]
        ax_main.scatter(xg, yg, color=color, edgecolor="black", linewidth=0.5,
                        s=50, alpha=0.75, zorder=3)
        if show_regression:
            res = stats.linregress(xg, yg)
            x_line = np.linspace(xlim[0], xlim[1], 100)
            y_line = res.slope * x_line + res.intercept
            ax_main.plot(x_line, y_line, color=color, linestyle="--", linewidth=1.4, zorder=2)

    if not show_regression:
        lo, hi = max(xlim[0], ylim[0]), min(xlim[1], ylim[1])
        ax_main.plot([lo, hi], [lo, hi], color="black", linestyle="--", linewidth=0.9, zorder=1)

    # Marginals.
    if marginal == "kde":
        for data, axis, vertical, color in [(x, ax_top, False, palette[0]), (y, ax_right, True, palette[0])]:
            kde = stats.gaussian_kde(data)
            grid = np.linspace(data.min(), data.max(), 200)
            density = kde(grid)
            if vertical:
                axis.fill_betweenx(grid, 0, density, color=color, alpha=0.35, edgecolor="black", linewidth=0.5)
                axis.set_xlim(0, density.max() * 1.3)
                axis.set_ylim(ylim)
            else:
                axis.fill_between(grid, 0, density, color=color, alpha=0.35, edgecolor="black", linewidth=0.5)
                axis.set_xlim(xlim)
                axis.set_ylim(0, density.max() * 1.3)
    elif marginal == "histogram":
        for data, axis, vertical, color in [(x, ax_top, False, palette[0]), (y, ax_right, True, palette[0])]:
            if vertical:
                axis.hist(data, bins=12, orientation="horizontal", color=color, alpha=0.55, edgecolor="white")
                axis.set_ylim(ylim)
            else:
                axis.hist(data, bins=12, color=color, alpha=0.55, edgecolor="white")
                axis.set_xlim(xlim)
    elif marginal == "boxplot":
        data_by_group = [y[groups == g] for g in unique_groups]
        positions = np.arange(1, len(unique_groups) + 1)
        _boxplot_mini(ax_right, data_by_group, positions, [color_map[g] for g in unique_groups])
        ax_right.set_ylim(ylim)
        ax_right.set_xlim(0.5, len(unique_groups) + 0.5)

    for ax in [ax_top, ax_right]:
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
    for spine in ["top", "right"]:
        ax_main.spines[spine].set_visible(False)

    ax_main.set_xlabel(xlabel or "", fontsize=9)
    ax_main.set_ylabel(ylabel or "", fontsize=9)
    ax_main.text(0.04, 0.96, label, transform=ax_main.transAxes,
                 fontsize=12, fontweight="bold", va="top")
    if annotation:
        ax_main.text(0.04, 0.82, annotation, transform=ax_main.transAxes,
                     fontsize=8.5, va="top")

    return ax_main


def plot_marginal_density_combo(
    df_top: pd.DataFrame,
    df_bottom: pd.DataFrame,
    figsize: Tuple[float, float] = (9, 9),
    save_path: Optional[str] = None,
) -> plt.Figure:
    fig = plt.figure(figsize=figsize)

    x = df_top["x"].to_numpy()
    y = df_top["y"].to_numpy()
    rmse = np.sqrt(np.mean((y - x) ** 2))

    _scatter_marginal_panel(
        fig, [0.08, 0.53, 0.40, 0.42],
        x, y, marginal="kde",
        label="(a)", xlabel="True", ylabel="Predicted",
        annotation=f"RMSE: {rmse:.2f}",
    )
    _scatter_marginal_panel(
        fig, [0.55, 0.53, 0.40, 0.42],
        x, y, marginal="histogram",
        label="(b)", xlabel="True", ylabel="Predicted",
    )

    x_g = df_bottom["x"].to_numpy()
    y_g = df_bottom["y"].to_numpy()
    groups = df_bottom["group"].to_numpy()
    palette = get_palette("soft_forest", n=len(set(groups)))

    _scatter_marginal_panel(
        fig, [0.08, 0.06, 0.40, 0.42],
        x_g, y_g, groups=groups, palette=palette, marginal="boxplot", show_regression=True,
        label="(c)", xlabel="X Value (units)", ylabel="Y Value (units)",
    )
    _scatter_marginal_panel(
        fig, [0.55, 0.06, 0.40, 0.42],
        x_g, y_g, groups=groups, palette=palette, marginal="histogram", show_regression=True,
        label="(d)", xlabel="X Value (units)", ylabel="Y Value (units)",
    )

    # Regression annotations for bottom panels (drawn on the figure via text).
    for i, g in enumerate(sorted(set(groups))):
        mask = groups == g
        res = stats.linregress(x_g[mask], y_g[mask])
        r2 = res.rvalue ** 2
        # Place text in the bottom-left panel area.
        fig.text(0.12, 0.38 - i * 0.03, f"Group {g+1}: $R^2$={r2:.3f}",
                 fontsize=9, color=palette[i % len(palette)], fontweight="bold")

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def make_demo_data(seed: int = 15) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    n = 120
    true = rng.uniform(15, 55, n)
    noise = rng.normal(0, 3, n)
    pred = true + noise
    df_top = pd.DataFrame({"x": true, "y": pred})

    n_g = 150
    group = np.repeat([0, 1, 2], n_g // 3)
    x_g = rng.uniform(5, 25, n_g)
    slopes = [0.8, 1.1, 0.6]
    intercepts = [5, 2, 8]
    y_g = np.array([slopes[g] * x_g[i] + intercepts[g] + rng.normal(0, 2)
                    for i, g in enumerate(group)])
    df_bottom = pd.DataFrame({"x": x_g, "y": y_g, "group": group})
    return df_top, df_bottom


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Scatter regression with marginal panels")
    parser.add_argument("--data-top", type=str, default=None, help="CSV with columns x,y (top row)")
    parser.add_argument("--data-bottom", type=str, default=None, help="CSV with columns x,y,group (bottom row)")
    parser.add_argument("--output", type=str, default="MarginalDensityCombo.png")
    args = parser.parse_args(argv)

    if args.data_top and args.data_bottom:
        df_top = pd.read_csv(args.data_top, encoding="utf-8-sig")
        df_bottom = pd.read_csv(args.data_bottom, encoding="utf-8-sig")
    else:
        df_top, df_bottom = make_demo_data()

    plot_marginal_density_combo(df_top, df_bottom, save_path=args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
