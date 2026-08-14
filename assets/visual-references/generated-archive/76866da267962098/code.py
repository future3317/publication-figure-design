# -*- coding: utf-8 -*-
"""Bar chart with gradient fill, error bars, value annotations and trend line.

Reproduces the WeChat reference style for a categorical bar chart:
  * vertical bars with a blue-to-red vertical gradient
  * error bars (vertical whiskers with caps)
  * numeric value labels above each bar
  * overlaid scatter points connected by a dashed trend line
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


def _configure_fonts() -> None:
    preferred = ["Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS"]
    available = {f.name for f in plt.matplotlib.font_manager.fontManager.ttflist}
    chosen = next((f for f in preferred if f in available), None)
    if chosen:
        plt.rcParams["font.family"] = [chosen, "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


_configure_fonts()


def _gradient_cmap(color_top: str, color_bottom: str, name: str = "grad") -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        name, [plt.matplotlib.colors.to_rgb(color_bottom), plt.matplotlib.colors.to_rgb(color_top)]
    )


def plot_gradient_bar_with_trend(
    df: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    err_col: str = "err",
    figsize: Tuple[float, float] = (8, 5.5),
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    x = np.arange(len(df))
    y = df[y_col].to_numpy()
    err = df[err_col].to_numpy()

    fig, ax = plt.subplots(figsize=figsize)

    # Per-bar gradient: color interpolates from blue (left/low) to red (right/high).
    cmap = _gradient_cmap("#B2182B", "#2166AC", name="br")
    bar_width = 0.7

    for i, (xi, yi, ei) in enumerate(zip(x, y, err)):
        color = cmap(i / max(len(df) - 1, 1))
        # Create a smooth vertical gradient image for each bar.
        n_steps = 256
        n_cols = 80
        grad = np.linspace(0, 1, n_steps).reshape(-1, 1)
        grad = np.tile(grad, (1, n_cols))
        ax.imshow(
            grad,
            extent=[xi - bar_width / 2, xi + bar_width / 2, 0, yi],
            aspect="auto",
            cmap=cmap,
            alpha=0.9,
            zorder=1,
            interpolation="bilinear",
        )
        # Bar border.
        rect = plt.Rectangle(
            (xi - bar_width / 2, 0), bar_width, yi,
            fill=False, edgecolor="lightgray", linewidth=0.8, zorder=2
        )
        ax.add_patch(rect)
        # Error bar.
        ax.errorbar(xi, yi, yerr=ei, color="black", capsize=4, capthick=1.2,
                    elinewidth=1.2, zorder=4)
        # Value label.
        ax.text(xi, yi + ei + 1.5, f"{yi:.1f}", ha="center", va="bottom",
                fontsize=10, color="black", zorder=5)

    # Trend scatter + dashed line.
    ax.scatter(x, y, color="#4A4A4A", s=50, zorder=5, edgecolor="white", linewidth=0.5)
    ax.plot(x, y, color="#4A4A4A", linestyle="--", linewidth=1.2, zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels(df[x_col], fontsize=10)
    ax.set_xlabel(xlabel or x_col, fontsize=12)
    ax.set_ylabel(ylabel or y_col, fontsize=12)
    ax.set_ylim(0, max(y + err) * 1.18)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
    ax.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig, ax


def make_demo_data(seed: int = 9) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = 12
    x = np.arange(1, n + 1)
    # Rise then fall pattern.
    y = 40 + 35 * np.sin((x - 1) / (n - 1) * np.pi) + rng.normal(0, 2, n)
    y = np.round(y, 1)
    err = rng.uniform(3, 8, n)
    err = np.round(err, 1)
    return pd.DataFrame({"x": x, "y": y, "err": err})


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Gradient bar chart with trend line")
    parser.add_argument("--data", type=str, default=None, help="CSV with columns x,y,err")
    parser.add_argument("--output", type=str, default="BarCategoricalGradient.png")
    args = parser.parse_args(argv)

    if args.data:
        df = pd.read_csv(args.data, encoding="utf-8-sig")
    else:
        df = make_demo_data()

    plot_gradient_bar_with_trend(
        df,
        xlabel="Sample(#)",
        ylabel="Current(A)",
        save_path=args.output,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
