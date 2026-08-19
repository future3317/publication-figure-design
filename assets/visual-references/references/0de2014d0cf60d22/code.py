#!/usr/bin/env python3
"""Synthetic reconstruction of a raw-point grouped comparison with significance brackets."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent


def add_bracket(ax, left, right, height, stars):
    ax.plot([left, left, right, right], [height - 2, height, height, height - 2],
            color="#171717", lw=1.5, clip_on=False)
    ax.text((left + right) / 2, height + 1.5, stars, ha="center", va="bottom",
            fontsize=10, fontweight="bold", color="#171717")


def main():
    rng = np.random.default_rng(14)
    groups = ["hCD45", "CD4", "CD8"]
    features = ["G1", "G2", "G3", "G4"]
    colors = ["#e7f0f8", "#c4d9ed", "#89acd4", "#59699e"]
    means = np.array([[88, 124, 112, 81], [25, 46, 35, 21], [52, 77, 59, 47]], dtype=float)
    values = [rng.normal(mean, max(3.0, mean * 0.12), 9) for row in means for mean in row]

    fig, ax = plt.subplots(figsize=(10.8, 7.1), dpi=300)
    x = np.arange(len(groups))
    width = 0.18
    for j, feature in enumerate(features):
        positions = x + (j - 1.5) * width
        for i, pos in enumerate(positions):
            sample = values[i * len(features) + j]
            ax.bar(pos, sample.mean(), width=width * 0.88, color=colors[j],
                   edgecolor=colors[j], linewidth=1.6, zorder=2, label=feature if i == 0 else None)
            jitter = rng.uniform(-width * 0.30, width * 0.30, len(sample))
            ax.scatter(pos + jitter, sample, s=42, facecolors="#ffffff",
                       edgecolors=colors[j], linewidths=1.2, zorder=3)

    add_bracket(ax, -0.30, 0.02, 178, "***")
    add_bracket(ax, -0.30, 0.55, 194, "**")
    add_bracket(ax, 0.05, 0.92, 210, "***")
    add_bracket(ax, 0.27, 0.72, 226, "***")
    add_bracket(ax, 1.00, 1.30, 62, "***")
    add_bracket(ax, 1.18, 1.66, 78, "***")
    add_bracket(ax, 1.42, 1.84, 94, "**")
    add_bracket(ax, 2.00, 2.30, 108, "***")
    add_bracket(ax, 2.20, 2.68, 124, "***")
    add_bracket(ax, 2.45, 2.85, 140, "*")

    ax.text(-0.42, 247, "ANOVA $P < 0.001$", fontsize=15, fontweight="bold")
    ax.text(1.02, 116, "Kruskal $P < 0.001$", fontsize=14, fontweight="bold")
    ax.text(-0.52, 264, "D", fontsize=25, fontweight="bold")
    ax.set_ylabel("Absolute number of indicated cells", fontsize=15, fontweight="bold")
    ax.set_xticks(x, groups, fontsize=17, fontweight="bold")
    ax.set_ylim(0, 270)
    ax.set_yticks(np.arange(0, 251, 50))
    ax.tick_params(axis="both", labelsize=12, width=1.5, length=6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.6)
    ax.spines["bottom"].set_linewidth(1.6)
    ax.legend(title="Features", loc="upper right", frameon=False, fontsize=11,
              title_fontsize=13, handlelength=1.5)
    fig.tight_layout()
    fig.savefig(ROOT / "reconstruction.png", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
