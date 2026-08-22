"""Independent synthetic reconstruction of the radial grouped-bar reference."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

OUT = Path(__file__).with_name("reconstruction.png")


def render(output: Path = OUT) -> None:
    labels = ["IIR", "EPE", "PHE", "RPF", "SIS", "IBI", "NDVI", "SAVI", "DUSI", "IEC", "FDI", "EPI"]
    values = np.array([
        [20.6, 17.3, 21.9], [23.1, 7.1, 14.2], [70.5, 21.1, 78.7],
        [709, 1177, 1427], [91.7, 56.7, 110.0], [11.5, 10.2, 13.8],
        [5.3, 2.4, 4.8], [565, 615, 282.7], [2691, 5382, 8072],
        [470, 314, 157], [894, 596, 298], [20.6, 17.3, 21.9],
    ])
    colors = ["#55c1ad", "#f59caf", "#8c7cc2"]
    sector_fill = ["#eaf6f2", "#fbeff3", "#f1edf8", "#fbf7e8"] * 3
    fig = plt.figure(figsize=(8.2, 8.2), dpi=180)
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.27)
    ax.set_axis_off()
    n = len(labels)
    step = 2 * np.pi / n
    gap = np.deg2rad(5.2)
    base = 0.37
    span = step - gap
    max_vals = values.max(axis=1)
    scaled = values / max_vals[:, None] * 0.73
    for i, (label, row) in enumerate(zip(labels, scaled)):
        theta = i * step
        ax.bar(theta, 0.73, width=span, bottom=base, color=sector_fill[i], alpha=.82,
               edgecolor="#222222", linewidth=1.1, zorder=1)
        for j, val in enumerate(row):
            offset = (j - 1) * span / 3.3
            width = span / 4.2
            ax.bar(theta + offset, val, width=width, bottom=base, color=colors[j],
                   edgecolor="#222222", linewidth=.9, zorder=3)
            r = base + val + .035
            rotation = np.degrees(theta + offset)
            if 90 < rotation < 270:
                rotation += 180
            ax.text(theta + offset, r, f"{values[i, j]:g}", ha="center", va="center",
                    fontsize=5.3, rotation=rotation, rotation_mode="anchor", color="#202020", zorder=5)
        rotation = np.degrees(theta)
        if 90 < rotation < 270:
            rotation += 180
        ax.text(theta, 1.19, label, ha="center", va="center", fontsize=7.6, weight="bold",
                rotation=rotation, rotation_mode="anchor", color="#171717")
    theta = np.linspace(0, 2 * np.pi, 240)
    ax.fill(theta, np.full_like(theta, .36), color="white", ec="#1f1f1f", lw=1.4, zorder=8)
    ax.fill(theta, np.full_like(theta, .33), color="white", ec="#777777", lw=.7, zorder=9)
    ax.text(0, 0, "Baseline", ha="center", va="center", fontsize=13, weight="bold", zorder=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors]
    fig.legend(handles, ["Beijing", "Tianjin", "Hebei"], loc="lower center", ncol=3,
               frameon=False, fontsize=8, bbox_to_anchor=(.5, -.015), handlelength=1.2)
    fig.tight_layout(pad=0.5)
    fig.subplots_adjust(bottom=.08)
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    Image.open(output).convert("RGB").resize((1440, 1496), Image.Resampling.LANCZOS).save(output)


if __name__ == "__main__":
    render()
