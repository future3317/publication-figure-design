#!/usr/bin/env python3
"""Synthetic reconstruction of a filled bubble radar chart with an inset donut."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent


def main():
    rng = np.random.default_rng(22)
    labels = ["BJ", "TJ", "HE", "SX", "IM", "LN", "JL", "HL", "SH", "JS", "ZJ", "AH",
              "FJ", "JX", "SD", "HA", "HB", "HN", "GX", "HI", "CQ", "SC", "GZ", "YN",
              "XZ", "SN", "GS", "QH", "NX", "XJ"]
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    colors = ["#33496b", "#e34b59", "#f2a15d"]
    values = [np.clip(rng.normal(base, 410, n), 1100, 6400)
              for base in (3500, 4100, 4700)]
    bubble = np.clip(rng.normal(6500, 260, n), 5700, 6900)

    fig = plt.figure(figsize=(10.6, 10.2), dpi=300)
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 7000)
    ax.set_yticks([2000, 4000, 6000])
    ax.set_yticklabels(["2000", "4000", "6000"], fontsize=10)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8)
    ax.grid(color="#aeb5bd", alpha=0.62, linewidth=0.8)
    ax.spines["polar"].set_linewidth(2.2)

    for year_values, color in zip(values, colors):
        closed = np.r_[year_values, year_values[0]]
        closed_angles = np.r_[angles, angles[0]]
        ax.plot(closed_angles, closed, color=color, linewidth=2.2, zorder=4)
        ax.fill(closed_angles, closed, color=color, alpha=0.22, zorder=2)
        ax.scatter(angles, year_values, s=42, color=color, alpha=0.64,
                   edgecolors=color, linewidths=0.6, zorder=5)
    ax.scatter(angles, bubble, s=(bubble / 82) ** 2, color="#34496b", alpha=0.63,
               edgecolors="#ffffff", linewidths=0.7, zorder=6)

    ax.scatter([0], [0], s=5700, color="white", edgecolors="black",
               linewidths=1.4, zorder=8)
    ax.text(0.5, 0.5, "Grain Yield\n(10k tons)", transform=ax.transAxes,
            ha="center", va="center", fontsize=14, zorder=9)
    handles = [plt.Line2D([0], [0], color=c, lw=7) for c in colors]
    ax.legend(handles, ["2020", "2010", "2000"], title="Year", loc="lower right",
              bbox_to_anchor=(1.28, 0.22), frameon=False, fontsize=10, title_fontsize=11)
    bubble_handles = [plt.scatter([], [], s=(s / 82) ** 2, color="#34496b", alpha=0.63,
                                  edgecolors="white") for s in (2000, 4000, 6000)]
    ax.legend(bubble_handles, ["2000", "4000", "6000"], title="Planting Area (Kha)",
              loc="upper right", bbox_to_anchor=(1.33, 0.84), frameon=False,
              fontsize=9, title_fontsize=10, scatterpoints=1)
    fig.text(0.95, 0.04, "Bubble size encodes planting area; fill encodes year.",
             ha="right", fontsize=8, color="#4d4d4d")
    fig.tight_layout()
    fig.savefig(ROOT / "reconstruction.png", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
