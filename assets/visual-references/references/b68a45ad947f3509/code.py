"""Independent synthetic reconstruction of a scatter + marginal-distribution reference."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from PIL import Image

OUT = Path(__file__).with_name("reconstruction.png")


def render(output: Path = OUT) -> None:
    rng = np.random.default_rng(7)
    groups = [("Grass", "#263653", 1.70, 2.0, 5.2), ("Land", "#e5a01c", 1.24, 4.2, 7.0),
              ("Water", "#bd1737", .91, 3.2, 6.0), ("Urban", "#9aa5b7", .44, 8.3, 5.5)]
    fig = plt.figure(figsize=(8.2, 7.5), dpi=180)
    gs = GridSpec(2, 2, figure=fig, width_ratios=[5.8, 1.0], height_ratios=[1.1, 5.8],
                  hspace=0.03, wspace=0.03)
    ax = fig.add_subplot(gs[1, 0])
    top = fig.add_subplot(gs[0, 0], sharex=ax)
    right = fig.add_subplot(gs[1, 1], sharey=ax)
    for name, color, slope, intercept, noise in groups:
        x = rng.uniform(4.4, 26.0, 27)
        y = slope * x / 1.5 + intercept + rng.normal(0, noise / 2.5, x.size)
        y = np.clip(y, 7.5, 27.7)
        coef = np.polyfit(x, y, 1)
        xx = np.linspace(x.min(), x.max(), 100)
        yy = np.polyval(coef, xx)
        resid = y - np.polyval(coef, x)
        band = 1.96 * np.std(resid) * np.sqrt(1 / len(x) + (xx - x.mean()) ** 2 / np.sum((x - x.mean()) ** 2))
        ax.fill_between(xx, yy - band, yy + band, color=color, alpha=.14, lw=0)
        ax.plot(xx, yy, color=color, lw=2.2, ls=(0, (5, 3)))
        ax.scatter(x, y, s=72, color=color, edgecolor="#343b4e", linewidth=.55, alpha=.88, zorder=3)
        bins = np.linspace(4, 27, 16)
        top.hist(x, bins=bins, color=color, alpha=.9, edgecolor="white", linewidth=.35)
        right.hist(y, bins=np.linspace(7, 28, 15), orientation="horizontal", color=color, alpha=.88,
                   edgecolor="white", linewidth=.35)
        ax.text(3.3, 27.0 - groups.index((name, color, slope, intercept, noise)) * .72,
                f"{name}: y = {slope:.2f}x + {intercept:.2f}, $R^2$ = {max(.25, 1-noise/10):.3f}, $p$ < 0.001",
                color=color, fontsize=9.2, weight="bold")
    ax.set_xlim(2.5, 28); ax.set_ylim(7.2, 28.8)
    ax.set_xlabel("GST", fontsize=12, weight="bold", labelpad=10)
    ax.set_ylabel("LST", fontsize=12, weight="bold", labelpad=10)
    for spine in ax.spines.values(): spine.set_linewidth(2.2)
    ax.tick_params(width=1.8, length=6, labelsize=9)
    top.axis("off"); right.axis("off")
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    Image.open(output).convert("RGB").resize((1440, 1326), Image.Resampling.LANCZOS).save(output)


if __name__ == "__main__":
    render()
