#!/usr/bin/env python3
"""Synthetic reconstruction of overlaid histograms with normal-fit curves."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent


def main():
    rng = np.random.default_rng(9)
    labels = ["Zhang et al.", "Kioumarsi et al.", "Xue et al."]
    colors = ["#e24a3b", "#263653", "#188f83"]
    params = [(-4.9, 14.4), (7.6, 25.1), (-3.3, 10.6)]
    # Keep the synthetic counts in the same visual range as the source (the
    # reference is a frequency histogram, not a density plot).
    sample_sizes = [95, 140, 95]
    samples = [rng.normal(mu, sigma, n) for (mu, sigma), n in zip(params, sample_sizes)]
    bins = np.linspace(-106.8, 106.8, 18)
    centers = (bins[:-1] + bins[1:]) / 2
    width = np.diff(bins).mean() * 0.28

    fig, ax = plt.subplots(figsize=(10.8, 7.1), dpi=300)
    for idx, (label, color, (mu, sigma), sample) in enumerate(zip(labels, colors, params, samples)):
        counts, _ = np.histogram(sample, bins=bins, density=False)
        ax.bar(centers + (idx - 1) * width, counts, width=width * 0.92,
               color=color, alpha=0.82, edgecolor="white", linewidth=0.7,
               label=f"{label} ($\\mu={mu:g}, \\sigma={sigma:g}$)", zorder=2)
        grid = np.linspace(-106.8, 106.8, 600)
        density = np.exp(-0.5 * ((grid - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
        expected_counts = density * len(sample) * np.diff(bins).mean()
        ax.plot(grid, expected_counts, color=color, linestyle="--", linewidth=3.0,
                label="Normal fits" if idx == 0 else None, zorder=3)

    ax.set_xlabel("Residual Group ($\\mu_{\\varepsilon}$)", fontsize=15, fontweight="bold")
    ax.set_ylabel("Frequency", fontsize=15, fontweight="bold")
    ax.set_xlim(-110, 110)
    ax.set_ylim(0, 48)
    ax.set_xticks(centers)
    ax.set_xticklabels([f"[{bins[i]:.1f}, {bins[i+1]:.1f})" for i in range(len(bins) - 1)],
                       rotation=42, ha="right", fontsize=9)
    ax.tick_params(axis="both", direction="in", top=True, right=True, width=1.5, length=6)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
    handles, legend_labels = ax.get_legend_handles_labels()
    normal_index = legend_labels.index("Normal fits")
    order = [i for i in range(len(handles)) if i != normal_index] + [normal_index]
    ax.legend([handles[i] for i in order], [legend_labels[i] for i in order],
              loc="upper left", frameon=True, framealpha=0.9, edgecolor="#666666",
              fontsize=10, handlelength=2.5)
    ax.text(0.91, 0.93, "(a)", transform=ax.transAxes, fontsize=28, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ROOT / "reconstruction.png", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
