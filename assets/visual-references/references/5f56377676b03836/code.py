"""Independent synthetic reconstruction of an annotated 3-D-looking pie chart."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from matplotlib.transforms import Affine2D
from PIL import Image

OUT = Path(__file__).with_name("reconstruction.png")


def _ellipse_pie(ax, values, colors, center, scale_y=.58, y=0, edge="white", lw=1.1):
    start = 90.0
    total = sum(values)
    for value, color in zip(values, colors):
        end = start - 360 * value / total
        wedge = Wedge(center, 1.0, end, start, facecolor=color, edgecolor=edge, linewidth=lw)
        wedge.set_transform(Affine2D().scale(1, scale_y) + ax.transData)
        wedge.set_center((center[0], center[1] + y))
        ax.add_patch(wedge)
        start = end


def render(output: Path = OUT) -> None:
    labels = ["GSR", "LST", "NDVI", "PRE", "ST", "ELEVATION", "SLOPE", "NDSI", "NIR", "NDWI", "WS", "NS", "NSC", "NSD", "ASPECT"]
    values = np.array([5.5, 7.6, 5.5, 3.8, 3.0, 18.5, 2.3, 11.8, 3.7, 22.8, 5.3, .4, 1.5, 7.7, .8])
    colors = ["#1e3b70", "#315fa5", "#458bc1", "#69a8c9", "#98c5d7", "#bdd2e5", "#d8e5f2", "#edf3fa",
              "#fff2df", "#f0c6aa", "#ee8a6d", "#ef4f41", "#dd2727", "#c51e25", "#a7191d"]
    fig, ax = plt.subplots(figsize=(9.5, 6.1), dpi=180)
    ax.set_xlim(-2.1, 2.1); ax.set_ylim(-1.2, 1.55); ax.axis("off")
    n = len(values); start = 90.0
    # Extruded depth layers, then the top ellipse.
    for depth in np.linspace(-.22, 0, 9):
        _ellipse_pie(ax, values, [(*plt.matplotlib.colors.to_rgb(c), .82) for c in colors], (0.35, depth), y=0)
    _ellipse_pie(ax, values, colors, (.35, .02), y=0, lw=1.6)
    start = 90.0
    for value, label in zip(values, labels):
        mid = np.deg2rad(start - 180 * value / values.sum())
        x, y = .35 + 1.16 * np.cos(mid), .02 + .68 * np.sin(mid)
        if value > 2.0:
            ax.text(x, y, f"{value:g}%", ha="center", va="center", fontsize=9, color="#252525")
        start -= 360 * value / values.sum()
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors]
    ax.legend(handles, labels, ncol=1, loc="center left", bbox_to_anchor=(-.02, .53), frameon=False,
              fontsize=8.5, handlelength=1.3, labelspacing=.78)
    ax.set_title("HHH YSHJXLXXZTHDSMYCSKYA (3D)", fontsize=18, pad=5)
    fig.subplots_adjust(left=.22, right=.98, top=.88, bottom=.03)
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    Image.open(output).convert("RGB").resize((1440, 964), Image.Resampling.LANCZOS).save(output)


if __name__ == "__main__":
    render()
