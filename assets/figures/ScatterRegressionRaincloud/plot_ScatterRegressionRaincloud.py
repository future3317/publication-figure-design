# -*- coding: utf-8 -*-
"""分组散点线性回归 + 箱线云雨图组合。

Reproduces a common academic figure layout:
  Left panel : grouped scatter with linear regression fits and 95% confidence
               bands, annotated with R² and p-value for each group.
  Right panel: half-violin / boxplot / jittered-scatter raincloud plot for the
               same groups, with pairwise independent t-test significance
               brackets (ns, *, **, ***).

Expected CSV format
-------------------
Three columns:  y | x | group
Example group names: "组1", "组2", "组3" or "CR", "PF", "G3".
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

# ---------------------------------------------------------------------------
# Font configuration (supports Chinese labels on Windows / common systems)
# ---------------------------------------------------------------------------

def _configure_fonts() -> None:
    """Select a CJK-compatible sans-serif font if available."""
    preferred = ["Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS"]
    available = {f.name for f in plt.matplotlib.font_manager.fontManager.ttflist}
    chosen = next((f for f in preferred if f in available), None)
    if chosen:
        plt.rcParams["font.family"] = [chosen, "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False

_configure_fonts()


# Try to reuse the skill palette manager; fall back to a built-in palette so
# the script can also run standalone.
try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from palette_manager import get_palette
except Exception:  # pragma: no cover
    def get_palette(name: str, n: Optional[int] = None) -> List[str]:
        """Minimal fallback categorical palette."""
        fallback = [
            "#377EB8", "#E41A1C", "#4DAF4A", "#984EA3",
            "#FF7F00", "#FFFF33", "#A65628", "#F781BF",
        ]
        if n is None:
            return fallback
        return [fallback[i % len(fallback)] for i in range(n)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _p_star_text(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def _regress_ci(
    x: np.ndarray,
    y: np.ndarray,
    x_pred: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (slope, intercept, predicted_y, lower_ci, upper_ci)."""
    x = np.asarray(x)
    y = np.asarray(y)
    n = len(x)
    res = stats.linregress(x, y)
    y_pred = res.slope * x_pred + res.intercept

    # Confidence band for the regression line (mean response CI).
    x_mean = x.mean()
    ssx = np.sum((x - x_mean) ** 2)
    df = max(n - 2, 1)
    t_val = stats.t.ppf(1 - alpha / 2, df)
    residuals = y - (res.slope * x + res.intercept)
    mse = np.sum(residuals**2) / df
    se = np.sqrt(mse * (1 / n + (x_pred - x_mean) ** 2 / ssx))
    ci = t_val * se
    return res, y_pred, y_pred - ci, y_pred + ci


def _half_violin(
    ax,
    data: Sequence[np.ndarray],
    positions: Sequence[float],
    colors: Sequence[str],
    side: str = "left",
    width: float = 0.6,
    alpha: float = 0.6,
    zorder: int = 1,
):
    """Draw half-violin bodies mirrored around each position."""
    for pos, vals, color in zip(positions, data, colors):
        vals = np.asarray(vals)
        kde = stats.gaussian_kde(vals)
        y_grid = np.linspace(vals.min(), vals.max(), 200)
        density = kde(y_grid)
        density = density / density.max() * (width / 2)

        if side == "left":
            x_fill = pos - density
        else:
            x_fill = pos + density

        ax.fill_betweenx(
            y_grid, pos, x_fill,
            color=color, alpha=alpha, edgecolor="black", linewidth=0.5, zorder=zorder,
        )
        # thin spine at the position
        ax.plot([pos, pos], [vals.min(), vals.max()], color="black", lw=0.5, zorder=zorder)


def _jittered_points(
    ax,
    data: Sequence[np.ndarray],
    positions: Sequence[float],
    colors: Sequence[str],
    marker: str = "o",
    size: int = 20,
    jitter: float = 0.05,
    alpha: float = 0.6,
    zorder: int = 3,
    seed: int = 42,
):
    rng = np.random.default_rng(seed)
    for pos, vals, color in zip(positions, data, colors):
        x_jitter = pos + rng.normal(0, jitter, len(vals))
        ax.scatter(x_jitter, vals, color=color, marker=marker, s=size,
                   edgecolor="white", linewidth=0.3, alpha=alpha, zorder=zorder)


def _boxplot(
    ax,
    data: Sequence[np.ndarray],
    positions: Sequence[float],
    colors: Sequence[str],
    widths: float = 0.18,
    zorder: int = 2,
):
    """Draw a minimal boxplot using patches (compatible with matplotlib 3.x)."""
    for pos, vals, color in zip(positions, data, colors):
        vals = np.asarray(vals)
        q1, med, q3 = np.percentile(vals, [25, 50, 75])
        iqr = q3 - q1
        lower = max(vals.min(), q1 - 1.5 * iqr)
        upper = min(vals.max(), q3 + 1.5 * iqr)

        # Box body: white face, group-colored edge.
        rect = Rectangle(
            (pos - widths / 2, q1), widths, q3 - q1,
            facecolor="white", edgecolor=color, linewidth=1.0, alpha=0.9, zorder=zorder
        )
        ax.add_patch(rect)

        # Median, whiskers, caps.
        ax.plot([pos - widths / 2, pos + widths / 2], [med, med],
                color="black", lw=1.2, zorder=zorder + 1)
        ax.plot([pos, pos], [lower, q1], color="black", lw=0.8, zorder=zorder)
        ax.plot([pos, pos], [q3, upper], color="black", lw=0.8, zorder=zorder)
        ax.plot([pos - widths / 4, pos + widths / 4], [lower, lower],
                color="black", lw=0.8, zorder=zorder)
        ax.plot([pos - widths / 4, pos + widths / 4], [upper, upper],
                color="black", lw=0.8, zorder=zorder)


# ---------------------------------------------------------------------------
# Main figure
# ---------------------------------------------------------------------------

def plot_scatter_regression_raincloud(
    df: pd.DataFrame,
    y_col: str = "y",
    x_col: str = "x",
    group_col: str = "group",
    groups_order: Optional[Sequence[str]] = None,
    palette: Optional[Sequence[str]] = None,
    markers: Optional[Sequence[str]] = None,
    figsize: Tuple[float, float] = (9, 4.2),
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    title: Optional[str] = None,
    compare_pairs: Optional[Sequence[Tuple[str, str]]] = None,
    p_text_size: float = 8.5,
    legend_loc: str = "upper right",
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, np.ndarray]:
    """Draw the grouped scatter-regression + raincloud combination figure.

    Parameters
    ----------
    df : pandas.DataFrame
        Data with at least three columns: y, x, group.
    groups_order : sequence of str, optional
        Order and selection of groups. If None, groups are sorted.
    palette : sequence of str, optional
        Explicit hex colors for groups. If None, uses the skill default
        categorical palette.
    markers : sequence of str, optional
        Matplotlib marker symbols for each group.
    compare_pairs : sequence of (str, str), optional
        Group pairs to test in the right panel. Defaults to adjacent pairs.
    """
    if groups_order is None:
        groups_order = sorted(df[group_col].unique())
    groups_order = list(groups_order)

    palette = palette or get_palette("watercolor_bloom", n=len(groups_order))
    markers = markers or ["o", "s", "^", "D", "v", "p", "h", "X"][:len(groups_order)]

    color_map: Dict[str, str] = {g: palette[i % len(palette)] for i, g in enumerate(groups_order)}
    marker_map: Dict[str, str] = {g: markers[i % len(markers)] for i, g in enumerate(groups_order)}

    data_by_group = [df[df[group_col] == g][[x_col, y_col]].dropna().values for g in groups_order]
    y_data = [d[:, 1] for d in data_by_group]

    fig, axes = plt.subplots(1, 2, figsize=figsize, gridspec_kw={"width_ratios": [1.35, 1]})
    ax_scatter, ax_rain = axes

    # ------------------------------------------------------------------
    # Left: scatter + regression
    # ------------------------------------------------------------------
    x_min = min(d[:, 0].min() for d in data_by_group)
    x_max = max(d[:, 0].max() for d in data_by_group)
    x_pad = 0.05 * (x_max - x_min)
    x_pred = np.linspace(x_min - x_pad, x_max + x_pad, 200)

    for g, (xy, color, marker) in enumerate(zip(data_by_group, palette, markers)):
        x_vals, y_vals = xy[:, 0], xy[:, 1]
        res, y_hat, y_lo, y_hi = _regress_ci(x_vals, y_vals, x_pred)
        r2 = res.rvalue**2
        pval = res.pvalue
        p_str = f"p < 0.001" if pval < 0.001 else f"p = {pval:.3f}"
        label = groups_order[g]

        ax_scatter.scatter(
            x_vals, y_vals, color=color, marker=marker,
            s=35, edgecolor="white", linewidth=0.4, alpha=0.7, zorder=3,
            label=label,
        )
        ax_scatter.plot(x_pred, y_hat, color=color, lw=1.6, zorder=2)
        ax_scatter.fill_between(x_pred, y_lo, y_hi, color=color, alpha=0.18, zorder=1)

        # Annotate regression statistics in group color at upper-left.
        text = f"{label}: $R^2$ = {r2:.2f}, {p_str}"
        ax_scatter.text(
            0.03, 0.97 - g * 0.09, text,
            transform=ax_scatter.transAxes,
            fontsize=p_text_size,
            color=color,
            verticalalignment="top",
        )

    ax_scatter.set_xlabel(xlabel or x_col, fontsize=10)
    ax_scatter.set_ylabel(ylabel or y_col, fontsize=10)
    ax_scatter.set_title(title or "", fontsize=11)
    ax_scatter.legend(loc=legend_loc, frameon=False, fontsize=8)
    ax_scatter.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
    for spine in ["top", "right"]:
        ax_scatter.spines[spine].set_visible(False)

    # ------------------------------------------------------------------
    # Right: half-violin + box + jitter raincloud
    # ------------------------------------------------------------------
    positions = np.arange(1, len(groups_order) + 1)
    _half_violin(ax_rain, y_data, positions, palette, side="right", width=0.55, alpha=0.5)
    _boxplot(ax_rain, y_data, positions, palette, widths=0.18)
    _jittered_points(ax_rain, y_data, positions, palette, jitter=0.06, size=18, alpha=0.55)

    ax_rain.set_xlim(0.4, len(groups_order) + 0.6)
    ax_rain.set_xticks(positions)
    ax_rain.set_xticklabels(groups_order, fontsize=9)
    ax_rain.set_ylabel(ylabel or y_col, fontsize=10)
    ax_rain.yaxis.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
    for spine in ["top", "right"]:
        ax_rain.spines[spine].set_visible(False)

    # Pairwise t-test brackets.
    if compare_pairs is None:
        compare_pairs = [(groups_order[i], groups_order[i + 1])
                         for i in range(len(groups_order) - 1)]

    y_top = max(y.max() for y in y_data)
    y_lo, y_hi = ax_rain.get_ylim()
    y_range = y_hi - y_lo
    bracket_y = y_top + 0.06 * y_range
    bracket_step = 0.055 * y_range

    for i, (a, b) in enumerate(compare_pairs):
        if a not in groups_order or b not in groups_order:
            continue
        idx_a, idx_b = groups_order.index(a), groups_order.index(b)
        ya, yb = y_data[idx_a], y_data[idx_b]
        _, pval = stats.ttest_ind(ya, yb, equal_var=False)
        x1, x2 = positions[idx_a], positions[idx_b]
        y_line = bracket_y + i * bracket_step
        ax_rain.plot([x1, x1, x2, x2], [y_line - bracket_step * 0.2, y_line, y_line, y_line - bracket_step * 0.2],
                     color="black", lw=0.9)
        ax_rain.text((x1 + x2) / 2, y_line + bracket_step * 0.05, _p_star_text(pval),
                     ha="center", va="bottom", fontsize=p_text_size)

    ax_rain.set_ylim(y_lo, bracket_y + len(compare_pairs) * bracket_step + 0.08 * y_range)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig, axes


def make_demo_data(n_per_group: int = 45, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records: List[Dict[str, float]] = []
    groups = ["组1", "组2", "组3"]
    base_slopes = [0.12, -0.08, 0.18]
    base_intercepts = [0.6, 2.0, 1.0]
    for g, slope, intercept in zip(groups, base_slopes, base_intercepts):
        x = rng.uniform(12, 22, n_per_group)
        y = intercept + slope * (x - 17) + rng.normal(0, 0.35, n_per_group)
        for xi, yi in zip(x, y):
            records.append({"y": yi, "x": xi, "group": g})
    return pd.DataFrame(records)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Grouped scatter regression + raincloud plot")
    parser.add_argument("--data", type=str, default=None, help="CSV with columns y,x,group")
    parser.add_argument("--output", type=str, default="ScatterRegressionRaincloud.png",
                        help="Output PNG path")
    parser.add_argument("--palette", type=str, default=None,
                        help="Palette ID (e.g., 'watercolor_bloom') or comma-separated hex colors")
    args = parser.parse_args(argv)

    if args.data:
        df = pd.read_csv(args.data)
    else:
        df = make_demo_data()

    palette: Optional[List[str]] = None
    if args.palette:
        if "," in args.palette:
            palette = [c.strip() for c in args.palette.split(",")]
        else:
            palette = get_palette(args.palette, n=df["group"].nunique())

    plot_scatter_regression_raincloud(
        df,
        y_col="y",
        x_col="x",
        group_col="group",
        xlabel="MAT (°C)",
        ylabel="MNN (mg·g⁻¹)",
        palette=palette,
        save_path=args.output,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
