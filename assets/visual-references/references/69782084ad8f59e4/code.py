"""Independent synthetic reconstruction of a two-panel PCoA ordination."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from PIL import Image

OUT = Path(__file__).with_name("reconstruction.png")


def render(output: Path = OUT) -> None:
    rng = np.random.default_rng(11)
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.5), dpi=180)
    palette = ["#eb8c7c", "#69bfd1"]
    for panel, ax in enumerate(axes):
        means = [(-.14, .02), (.12, .03)]
        for i, (mx, my) in enumerate(means):
            pts = rng.multivariate_normal([mx, my], [[.004, 0], [0, .010]], 48)
            if panel == 1: pts[:, 0] += .025 * (i * 2 - 1)
            ax.scatter(pts[:, 0], pts[:, 1], s=42, color=palette[i], alpha=.9,
                       edgecolor="white", linewidth=.35, label=["Control", "T2D"][i])
            ax.add_patch(Ellipse((pts[:, 0].mean(), pts[:, 1].mean()), .25, .42,
                                 facecolor=palette[i], edgecolor=palette[i], alpha=.18, lw=1.5))
        ax.axhline(0, color="#999999", ls="--", lw=.8); ax.axvline(0, color="#999999", ls="--", lw=.8)
        ax.set_xlim(-.42, .42); ax.set_ylim(-.34, .34)
        ax.set_xlabel(f"PCoA1 ({10.25-panel*3.92:.2f}%)", fontsize=10, weight="bold")
        ax.set_ylabel(f"PCoA2 ({3.31+panel*.50:.2f}%)", fontsize=10, weight="bold")
        ax.set_title(["PCoA_bray curtis", "PCoA_jaccard"][panel], fontsize=12, weight="bold")
        ax.text(-.39, .27, "PERMANOVA\n$R^2$ = " + ["0.101", "0.055"][panel] + "\n$P$ = 0.001",
                fontsize=9.5, weight="bold", va="top")
        ax.text(-.40, .37, "AB"[panel], fontsize=15, weight="bold")
        ax.tick_params(labelsize=8.5, width=1.2)
        for spine in ax.spines.values(): spine.set_linewidth(1.4)
        if panel == 0: ax.legend(loc="lower left", frameon=True, fontsize=8)
    fig.tight_layout(w_pad=1.5)
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    Image.open(output).convert("RGB").resize((1440, 654), Image.Resampling.LANCZOS).save(output)


if __name__ == "__main__":
    render()
