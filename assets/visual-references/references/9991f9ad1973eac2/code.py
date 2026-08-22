"""Independent synthetic reconstruction of nested semi-circular arcs and bars."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Rectangle
from PIL import Image

OUT = Path(__file__).with_name("reconstruction.png")


def render(output: Path = OUT) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 5.9), dpi=180)
    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-.5, 1.35); ax.axis("off")
    arcs = [("Saitama", .97, 178, "#e8a0bd", "43%"), ("", .75, 160, "#334a8a", "47%"),
            ("", .48, 104, "#e6a18e", "8%"), ("", .28, 38, "#9b93bc", "3%")]
    for label, radius, extent, color, value in arcs:
        ax.add_patch(Wedge((0, 0), radius, 0, extent, width=.16, facecolor=color, edgecolor="white", lw=2))
        if label: ax.text(0, radius + .09, label, ha="center", va="center", fontsize=13, weight="bold")
        if value: ax.text(radius*.55, radius*.38, value, ha="center", va="center", fontsize=11,
                          color="white" if color in {"#e8a0bd", "#334a8a"} else "#252525")
    bar_y = -.17; starts = [-.97, -.18, .49]; widths = [.80, .34, .45]
    bar_colors = ["#9cb5d2", "#f2c9bd", "#aaa4c8"]
    for x, w, c, value in zip(starts, widths, bar_colors, ["47%", "25%", "28%"]):
        ax.add_patch(Rectangle((x, bar_y), w, .16, facecolor=c, edgecolor="white", lw=2))
        ax.text(x+w/2, bar_y+.08, value, ha="center", va="center", fontsize=10,
                color="white" if c != "#f2c9bd" else "#333333")
    handles = [Rectangle((0, 0), 1, 1, color=c) for c in ["#e8a0bd", "#334a8a", "#e6a18e", "#9b93bc", *bar_colors]]
    labels = ["Arc_Outer", "Arc_Mid", "Arc_Inner1", "Arc_Inner2", "Bar_1", "Bar_2", "Bar_3"]
    ax.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, -.34), ncol=4,
              frameon=False, fontsize=8.5, handlelength=1.4)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    Image.open(output).convert("RGB").resize((1088, 878), Image.Resampling.LANCZOS).save(output)


if __name__ == "__main__":
    render()
