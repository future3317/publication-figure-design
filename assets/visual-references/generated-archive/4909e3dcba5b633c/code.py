# -*- coding: utf-8 -*-
"""Bar chart with grouped facets and individual data-point swarm overlay.

Reproduces the WeChat reference style:
  * bars coloured by category / marker
  * one beeswarm / strip of individual points on top of each bar
  * facet groups separated by a bold horizontal span label (e.g. dorsal / ventral)
  * thick baseline, no top/right spines
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from palette_manager import get_palette
except Exception:  # pragma: no cover
    def get_palette(name: str, n: Optional[int] = None) -> List[str]:
        fallback = ["#5B79A2", "#E8976A", "#6BAF72", "#C75B6B",
                    "#8E7CC3", "#9E9E9E", "#E8C547", "#5DBCD2", "#7D7D7D"]
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


def plot_bar_with_swarm(
    df: pd.DataFrame,
    marker_col: str = "marker",
    value_col: str = "value",
    facet_col: str = "facet",
    palette: Optional[Sequence[str]] = None,
    figsize: Tuple[float, float] = (8.5, 5.5),
    ylabel: Optional[str] = None,
    title_y: float = 0.98,
    swarm_jitter: float = 0.11,
    swarm_size: int = 55,
    swarm_alpha: float = 0.85,
    bar_width: float = 0.55,
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Draw a faceted bar chart with swarm overlay.

    Parameters
    ----------
    df : pandas.DataFrame
        Expected columns: marker, value, facet.
    """
    # Preserve input order if possible.
    if isinstance(df[facet_col].dtype, pd.CategoricalDtype):
        facets = df[facet_col].cat.categories.tolist()
    else:
        facets = list(dict.fromkeys(df[facet_col]))

    all_markers = list(dict.fromkeys(df[marker_col]))
    palette = palette or get_palette("pastel_girl", n=len(all_markers))
    color_map: Dict[str, str] = {m: palette[i % len(palette)] for i, m in enumerate(all_markers)}

    fig, ax = plt.subplots(figsize=figsize)

    x_pos = 0
    x_labels: List[str] = []
    x_label_pos: List[float] = []
    facet_centers: Dict[str, float] = {}
    facet_widths: Dict[str, Tuple[float, float]] = {}
    group_start = 0

    rng = np.random.default_rng(42)

    for facet in facets:
        sub = df[df[facet_col] == facet]
        markers = list(dict.fromkeys(sub[marker_col]))
        group_start = x_pos

        for marker in markers:
            vals = sub[sub[marker_col] == marker][value_col].dropna().to_numpy()
            color = color_map[marker]
            # Bar
            bar_height = vals.mean()
            ax.bar(x_pos, bar_height, width=bar_width, color=color, edgecolor="black",
                   linewidth=1.2, alpha=0.85, zorder=2)
            # Swarm points
            jitter = rng.uniform(-swarm_jitter, swarm_jitter, len(vals))
            ax.scatter(np.full_like(vals, x_pos) + jitter, vals,
                       color=color, edgecolor="black", linewidth=0.6,
                       s=swarm_size, alpha=swarm_alpha, zorder=3)

            x_labels.append(marker)
            x_label_pos.append(x_pos)
            x_pos += 1

        facet_centers[facet] = (group_start + x_pos - 1) / 2
        facet_widths[facet] = (group_start - 0.35, x_pos - 1 + 0.35)
        x_pos += 0.8  # gap between facets

    # Facet titles and horizontal brackets.
    y_max = ax.get_ylim()[1]
    for facet, center in facet_centers.items():
        ax.text(center, title_y * y_max, facet, ha="center", va="bottom",
                fontsize=13, fontweight="bold", color="black")
        x0, x1 = facet_widths[facet]
        ax.plot([x0, x1], [title_y * y_max - 0.02 * y_max] * 2,
                color="black", lw=2.5, solid_capstyle="butt")

    ax.set_xticks(x_label_pos)
    ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=10)
    ax.set_ylabel(ylabel or value_col, fontsize=12)
    ax.set_ylim(0, y_max * 1.08)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
    ax.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_linewidth(1.5)
    ax.spines["bottom"].set_linewidth(1.5)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig, ax


def make_demo_data(seed: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    markers_dorsal = ["PAX6", "EMX2", "TBR2", "MAP2"]
    markers_ventral = ["NKX2-1", "OLIG2", "DLX2", "GAD67", "GAD65"]
    means_dorsal = [42, 44, 22, 22]
    means_ventral = [45, 24, 43, 46, 22]
    records = []
    for marker, mean in zip(markers_dorsal, means_dorsal):
        for _ in range(25):
            records.append({"marker": marker, "value": rng.normal(mean, 4.5), "facet": "dorsal"})
    for marker, mean in zip(markers_ventral, means_ventral):
        for _ in range(25):
            records.append({"marker": marker, "value": rng.normal(mean, 4.5), "facet": "ventral"})
    return pd.DataFrame(records)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Faceted bar chart with swarm overlay")
    parser.add_argument("--data", type=str, default=None, help="CSV with columns marker,value,facet")
    parser.add_argument("--output", type=str, default="BarWithSwarm.png")
    parser.add_argument("--palette", type=str, default=None)
    args = parser.parse_args(argv)

    if args.data:
        df = pd.read_csv(args.data, encoding="utf-8-sig")
    else:
        df = make_demo_data()

    palette = None
    if args.palette:
        palette = [c.strip() for c in args.palette.split(",")] if "," in args.palette else get_palette(args.palette, n=df["marker"].nunique())

    plot_bar_with_swarm(
        df,
        marker_col="marker",
        value_col="value",
        facet_col="facet",
        ylabel="marker composition (%)",
        palette=palette,
        save_path=args.output,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
