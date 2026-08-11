# -*- coding: utf-8 -*-
"""Generate synthetic visual references based on the figures4papers / Scientific
Figure Making house style, then ingest them into the academic-figure-skill
Visual Reference Library.

The original Scientific Figure Making skill has no local example images; its
demos are links to the figures4papers GitHub repository. To honor the user's
request to add example figures to our library, these synthetic redraws follow
the documented style using made-up data so they can be redistributed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure skill scripts are importable.
skill_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(skill_root / "scripts"))

from reference_library import ingest_image


# Figures4papers semantic palette.
PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_3": "#8BCF8B",
    "red_strong": "#B64342",
    "neutral": "#CFCECE",
}


def _apply_pub_style(font_size: int = 16, axes_linewidth: float = 2.5):
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": font_size,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": axes_linewidth,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": axes_linewidth * 0.6,
        "ytick.major.width": axes_linewidth * 0.6,
        "legend.frameon": False,
    })


def generate_grouped_bar(out_path: Path) -> None:
    """Grouped bar with publication style: large fonts, black edges, annotations."""
    _apply_pub_style(font_size=20, axes_linewidth=2.5)
    categories = ["Metric A", "Metric B", "Metric C", "Metric D"]
    values = {
        "Ours": [0.92, 0.88, 0.85, 0.90],
        "Baseline X": [0.85, 0.82, 0.88, 0.84],
        "Baseline Y": [0.78, 0.80, 0.82, 0.79],
    }
    colors = [PALETTE["blue_main"], PALETTE["green_3"], PALETTE["red_strong"]]

    fig, ax = plt.subplots(figsize=(12, 5))
    n_series = len(values)
    n_cats = len(categories)
    bar_width = 0.25
    x = np.arange(n_cats)

    for i, (label, vals) in enumerate(values.items()):
        bars = ax.bar(x + (i - n_series / 2 + 0.5) * bar_width, vals,
                      width=bar_width, label=label, color=colors[i],
                      edgecolor="black", linewidth=1.5)
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height,
                    f"{height:.2f}", ha="center", va="bottom", fontsize=12)

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel("Score")
    ax.set_ylim(0.7, 1.0)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.0))
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    plt.rcdefaults()


def generate_trend_legend_panel(out_path: Path) -> None:
    """Two trend panels + one dedicated legend panel."""
    _apply_pub_style(font_size=14, axes_linewidth=2.0)
    x = np.linspace(0, 10, 50)
    y1 = 0.5 + 0.4 * (1 - np.exp(-x / 3))
    y2 = 0.45 + 0.35 * (1 - np.exp(-x / 4))

    fig, axes = plt.subplots(1, 3, figsize=(14, 4),
                             gridspec_kw={"width_ratios": [1, 1, 0.4]})

    for ax, y_a, y_b, title in [(axes[0], y1, y2, "Training"),
                                 (axes[1], y1 * 1.1, y2 * 1.05, "Validation")]:
        ax.plot(x, y_a, color=PALETTE["blue_main"], linewidth=2.5, label="Model A")
        ax.fill_between(x, y_a - 0.02, y_a + 0.02, color=PALETTE["blue_main"], alpha=0.2)
        ax.plot(x, y_b, color=PALETTE["red_strong"], linewidth=2.5, label="Model B")
        ax.fill_between(x, y_b - 0.02, y_b + 0.02, color=PALETTE["red_strong"], alpha=0.2)
        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Step")
        ax.set_ylabel("Loss")
        ax.set_ylim(0.4, 1.0)

    axes[2].set_axis_off()
    handles, labels = axes[0].get_legend_handles_labels()
    axes[2].legend(handles, labels, loc="center", frameon=False, fontsize=12)

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    plt.rcdefaults()


def generate_heatmap(out_path: Path) -> None:
    """Heatmap with row/column labels and colorbar."""
    _apply_pub_style(font_size=12, axes_linewidth=2.0)
    rng = np.random.default_rng(42)
    n = 8
    matrix = rng.random((n, n))
    matrix = (matrix + matrix.T) / 2
    labels = [f"F{i+1}" for i in range(n)]

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(matrix, cmap="magma", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_yticklabels(labels, fontsize=10)
    fig.colorbar(im, ax=ax, label="Correlation")
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    plt.rcdefaults()


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    references = [
        (
            out_dir / "pub_grouped_bar.png",
            generate_grouped_bar,
            {
                "figure_type": "BarComparison",
                "subtype": "figures4papers_grouped_bar",
                "tags": ["figures4papers", "publication-style", "grouped-bar", "annotation", "semantic-colors"],
                "palette": None,
                "palette_policy": "preserve",
                "layout": "1x1",
                "journal_style": "Nature",
                "source": "figures4papers house style (synthetic redraw)",
                "source_url": "https://github.com/ChenLiu-1996/figures4papers",
                "license": "synthetic-redraw",
                "usage_scope": "redistributable",
                "n_groups": 3,
                "data_density": "low",
                "review_status": "reviewed",
                "aesthetic_rating": 4,
                "production_ready": False,
                "notes": "Synthetic redraw of figures4papers grouped-bar style: large fonts, black edges, direct value annotations, semantic colors. Borrow layout and encoding, not data.",
            },
        ),
        (
            out_dir / "pub_trend_legend_panel.png",
            generate_trend_legend_panel,
            {
                "figure_type": "LineTrend",
                "subtype": "figures4papers_trend_legend_panel",
                "tags": ["figures4papers", "publication-style", "line-trend", "multi-panel", "dedicated-legend"],
                "palette": None,
                "palette_policy": "preserve",
                "layout": "1x3",
                "journal_style": "Nature",
                "source": "figures4papers house style (synthetic redraw)",
                "source_url": "https://github.com/ChenLiu-1996/figures4papers",
                "license": "synthetic-redraw",
                "usage_scope": "redistributable",
                "n_groups": 2,
                "data_density": "medium",
                "review_status": "reviewed",
                "aesthetic_rating": 4,
                "production_ready": False,
                "notes": "Synthetic redraw of figures4papers multi-panel trend style: two data panels + one dedicated legend-only panel. Borrow layout and legend strategy, not data.",
            },
        ),
        (
            out_dir / "pub_heatmap.png",
            generate_heatmap,
            {
                "figure_type": "heatmap",
                "subtype": "figures4papers_heatmap",
                "tags": ["figures4papers", "publication-style", "heatmap", "magma", "correlation"],
                "palette": None,
                "palette_policy": "preserve",
                "layout": "1x1",
                "journal_style": "Nature",
                "source": "figures4papers house style (synthetic redraw)",
                "source_url": "https://github.com/ChenLiu-1996/figures4papers",
                "license": "synthetic-redraw",
                "usage_scope": "redistributable",
                "n_groups": 8,
                "data_density": "medium",
                "review_status": "reviewed",
                "aesthetic_rating": 3.5,
                "production_ready": False,
                "notes": "Synthetic redraw of figures4papers heatmap style: symmetric matrix, row/column labels, colorbar. Borrow layout and colormap treatment, not data.",
            },
        ),
    ]

    for out_path, generator, meta in references:
        generator(out_path)
        ref = ingest_image(
            image_path=out_path,
            figure_type=meta["figure_type"],
            metadata_override=meta,
        )
        print(f"Ingested {ref.id}: {ref.metadata['figure_type']} ({ref.metadata.get('subtype')})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
