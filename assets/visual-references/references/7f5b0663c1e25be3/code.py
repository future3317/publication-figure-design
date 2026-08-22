"""Independent synthetic reconstruction of paired violin/box/raw-point comparisons."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

OUT = Path(__file__).with_name("reconstruction.png")


def render(output: Path = OUT) -> None:
    rng = np.random.default_rng(19)
    colors = ["#f08d9e", "#6f9dbd"]
    data = [[rng.normal(2.75, .30, 34), rng.normal(3.02, .38, 34)],
            [rng.normal(3.62, .35, 34), rng.normal(2.65, .30, 34)]]
    fig, ax = plt.subplots(figsize=(7.3, 8.1), dpi=180)
    positions = [1.0, 1.35, 3.25, 3.60]
    for idx, (pair, center) in enumerate(zip(data, [1.18, 3.43])):
        vp = ax.violinplot(pair, positions=positions[idx*2:idx*2+2], widths=.48, showextrema=False)
        for body, color in zip(vp["bodies"], colors):
            body.set_facecolor(color); body.set_edgecolor(color); body.set_alpha(.68); body.set_linewidth(1.4)
        bp = ax.boxplot(pair, positions=positions[idx*2:idx*2+2], widths=.18, patch_artist=True,
                        showfliers=False, medianprops={"color": "white", "lw": 1.2},
                        whiskerprops={"lw": 1.5}, capprops={"lw": 1.5})
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color); patch.set_edgecolor(color); patch.set_alpha(.82)
        means = [np.mean(x) for x in pair]
        ax.plot(positions[idx*2:idx*2+2], means, color="#b82f46" if idx else "#1d5f89", lw=1.7,
                marker="D", ms=7, zorder=4)
        for x, vals, color in zip(positions[idx*2:idx*2+2], pair, colors):
            jitter = rng.normal(0, .035, len(vals))
            ax.scatter(x + jitter, vals, s=28, facecolor=color, edgecolor=color, alpha=.78, zorder=5)
    ax.set_xlim(.45, 4.15); ax.set_ylim(1.95, 4.68)
    ax.set_xticks([1.18, 3.43], ["Pre", "Post"], fontsize=11)
    ax.set_xlabel("Fertilizer Treatment", fontsize=13, weight="bold", labelpad=16)
    ax.set_ylabel("Sepal Width", fontsize=13, weight="bold")
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=c) for c in colors], ["Versicolor", "Virginica"],
              title="Flower Species", frameon=False, loc="upper right", fontsize=9, title_fontsize=10)
    ax.tick_params(width=1.5, length=5, labelsize=9)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    Image.open(output).convert("RGB").resize((1440, 1592), Image.Resampling.LANCZOS).save(output)


if __name__ == "__main__":
    render()
