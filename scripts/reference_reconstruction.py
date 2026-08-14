"""Small synthetic-data renderers for user-supplied visual references.

These renderers intentionally reproduce visual grammar (topology, marks, hierarchy,
and annotation style), not the unavailable source data behind a pasted image.
Each reference-local ``code.py`` delegates here with a stable reference id.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


PALETTE = ["#1f4e79", "#d95f02", "#2ca25f", "#756bb1", "#e7298a"]


def _finish(fig: plt.Figure, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _style(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#d9dee5", lw=0.6, alpha=0.65)
    ax.tick_params(labelsize=8)


def learning_curves(output: Path) -> None:
    x = np.linspace(0, 100, 120)
    rng = np.random.default_rng(4)
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 5.8), sharex=True)
    for i, (ax, title, base) in enumerate(zip(axes.ravel(), ["Train loss", "Validation loss", "Train accuracy", "Validation accuracy"], [1.3, 1.15, 0.55, 0.45])):
        if i < 2:
            mean = 0.12 + base * np.exp(-x / (28 + i * 3))
            spread = 0.025 + 0.015 * np.exp(-x / 35)
        else:
            mean = 0.95 - base * np.exp(-x / (30 + i))
            spread = 0.018 + 0.012 * np.exp(-x / 35)
        ax.fill_between(x, mean - spread, mean + spread, color=PALETTE[i], alpha=0.18)
        ax.plot(x, mean, color=PALETTE[i], lw=2.2, label="mean")
        for fold in range(3):
            ax.plot(x, mean + rng.normal(0, spread / 2, len(x)), color=PALETTE[i], alpha=0.22, lw=0.8)
        ax.set_title(title, fontsize=10, loc="left", weight="bold")
        ax.legend(frameon=False, fontsize=7, loc="best")
        _style(ax)
    axes[1, 0].set_xlabel("Epoch")
    axes[1, 1].set_xlabel("Epoch")
    fig.tight_layout(w_pad=1.3, h_pad=1.1)
    _finish(fig, output)


def multi_panel_line_comparison(output: Path) -> None:
    x = np.linspace(0, 1, 80)
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.1), sharey=True)
    for j, ax in enumerate(axes):
        for i, color in enumerate(PALETTE[:3]):
            y = (0.35 + i * 0.1) + (0.35 + 0.05 * j) * x ** (0.7 + i * 0.3)
            ax.fill_between(x, y - 0.025, y + 0.025, color=color, alpha=0.12)
            ax.plot(x, y, color=color, lw=1.8, label=f"Model {i + 1}")
        ax.axhline(0.55, color="#555b66", ls="--", lw=1, label="reference" if j == 0 else None)
        ax.scatter([0.72], [0.73 + j * 0.02], s=28, color="#111827", zorder=4)
        ax.set_title(["Low composition", "Medium composition", "High composition"][j], fontsize=9, weight="bold")
        ax.set_xlabel("Composition")
        _style(ax)
    axes[0].set_ylabel("Score")
    axes[0].legend(frameon=False, fontsize=7, ncol=2, loc="upper left")
    fig.tight_layout()
    _finish(fig, output)


def scatter_marginal(output: Path) -> None:
    rng = np.random.default_rng(7)
    groups = [rng.normal((0.25, 0.35), (0.10, 0.09), (100, 2)), rng.normal((0.62, 0.58), (0.11, 0.10), (100, 2)), rng.normal((0.78, 0.27), (0.08, 0.12), (100, 2))]
    fig = plt.figure(figsize=(5.7, 5.2))
    gs = fig.add_gridspec(4, 4, hspace=0.05, wspace=0.05)
    ax = fig.add_subplot(gs[1:, :3]); top = fig.add_subplot(gs[0, :3], sharex=ax); right = fig.add_subplot(gs[1:, 3], sharey=ax)
    for i, data in enumerate(groups):
        c = PALETTE[i]
        ax.scatter(data[:, 0], data[:, 1], s=12, alpha=0.5, color=c, label=f"Group {i + 1}")
        top.hist(data[:, 0], bins=18, density=True, color=c, alpha=0.30)
        right.hist(data[:, 1], bins=18, density=True, orientation="horizontal", color=c, alpha=0.30)
    ax.plot([0, 1], [0, 1], ls="--", color="#343a40", lw=1)
    ax.axvline(0.5, color="#8b95a1", lw=0.8); ax.axhline(0.5, color="#8b95a1", lw=0.8)
    ax.set(xlabel="Reference", ylabel="Prediction", xlim=(0, 1), ylim=(0, 1))
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    top.tick_params(labelbottom=False); right.tick_params(labelleft=False)
    for a in (ax, top, right):
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _finish(fig, output)


def mixed_statistics_grid(output: Path) -> None:
    rng = np.random.default_rng(9)
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.8))
    ax = axes[0, 0]; y = np.arange(4); effect = np.array([0.28, -0.12, 0.41, 0.08]); err = np.array([0.10, 0.08, 0.13, 0.07]); ax.errorbar(effect, y, xerr=err, fmt="o", color=PALETTE[0], capsize=3); ax.axvline(0, color="#555", lw=0.8, ls="--"); ax.set_yticks(y, ["A", "B", "C", "D"]); ax.set_title("Effect estimates", loc="left", weight="bold", fontsize=9); _style(ax)
    ax = axes[0, 1]; vals = [rng.normal(0.35, .08, 30), rng.normal(0.55, .1, 30), rng.normal(0.68, .07, 30)]; ax.boxplot(vals, patch_artist=True, boxprops={"facecolor": "#cbd5e1", "alpha": .8}); ax.set_xticks([1, 2, 3], ["A", "B", "C"]); ax.set_title("Distribution comparison", loc="left", weight="bold", fontsize=9); _style(ax)
    ax = axes[1, 0]; bars = ax.bar(["A", "B", "C"], [0.42, 0.68, 0.57], color=PALETTE[:3], alpha=.85); ax.bar_label(bars, fmt="%.2f", fontsize=7, padding=2); ax.set_ylim(0, .85); ax.set_title("Annotated groups", loc="left", weight="bold", fontsize=9); _style(ax)
    ax = axes[1, 1]; vals = [rng.normal(.28, .04, 25), rng.normal(.46, .06, 25), rng.normal(.62, .05, 25)]; ax.boxplot(vals, patch_artist=True, widths=.55, boxprops={"facecolor": "#dbeafe", "alpha": .85}, medianprops={"color": PALETTE[3], "lw": 1.8}); ax.scatter([1, 2, 3], [.28, .46, .62], color=PALETTE[3], s=24, zorder=3); ax.set_xticks([1, 2, 3], ["A", "B", "C"]); ax.set_title("Grouped summary", loc="left", weight="bold", fontsize=9); _style(ax)
    fig.tight_layout()
    _finish(fig, output)


def mixed_multi_panel(output: Path) -> None:
    fig = plt.figure(figsize=(9.0, 5.8)); gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1], height_ratios=[1, 1.25], hspace=.35, wspace=.3)
    ax = fig.add_subplot(gs[0, 0]); names = ["Signal 1", "Signal 2", "Signal 3", "Signal 4"]; ax.barh(names, [0.72, .46, .85, .58], color=[PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3]]); ax.set_title("Enrichment", loc="left", weight="bold", fontsize=9); _style(ax)
    ax = fig.add_subplot(gs[0, 1]); y0 = np.linspace(.72, .99, 120); y1 = np.linspace(.58, .82, 120); ax.fill_between(y0, np.arange(120) * 0 + 0.55, np.arange(120) * 0 + 0.78, color="#f2b84b", alpha=.85); ax.fill_between(y1, np.arange(120) * 0 + 0.05, np.arange(120) * 0 + 0.28, color="#e9784f", alpha=.88); ax.set_yticks([.16, .66], ["Permuted", "Original"]); ax.set_xlabel("Train ROC-AUC"); ax.set_title("ROC density", loc="left", weight="bold", fontsize=9); _style(ax)
    ax = fig.add_subplot(gs[1, 0], projection="polar"); theta = np.linspace(0, 2 * np.pi, 24, endpoint=False); radii = np.array([.4, .65, .5, .78, .55, .72, .35, .62] * 3); ax.bar(theta, radii, width=.22, color=[PALETTE[0]] * 8 + [PALETTE[1]] * 8 + [PALETTE[3]] * 8, alpha=.78); ax.set_title("Category composition", fontsize=9, pad=14, weight="bold"); ax.set_yticklabels([])
    axes = fig.add_subplot(gs[1, 1]); axes.axis("off"); axes.text(.05, .9, "Three-panel assembly", weight="bold", fontsize=10); axes.text(.05, .72, "bar enrichment\ntrain-vs-permuted density\nradial category summary", fontsize=9, va="top", linespacing=1.6)
    fig.tight_layout()
    _finish(fig, output)


def grouped_bar_inset(output: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.8, 4.4)); x = np.arange(5); width=.07
    series = [("BF16", PALETTE[0]), ("FP16", PALETTE[2]), ("FP32", "#e85d5d")]
    for group, (precision, c) in enumerate(series):
        for model in range(4):
            vals = .38 + .07 * model + .045 * group + np.array([.08, .01, .12, .06, .15]) * (1 - model * .08)
            offset = (group * 4 + model - 5.5) * width
            ax.bar(x + offset, vals, width, color=c, alpha=.75 - model * .08, label=f"{precision} model {model + 1}")
    ax.set_xticks(x, ["Data A", "Data B", "Data C", "Data D", "Data E"]); ax.set_ylabel("Score"); ax.legend(frameon=False, fontsize=6, ncol=4, loc="upper left"); ax.set_title("Benchmark comparison with precision-specific insets", loc="left", weight="bold", fontsize=10); _style(ax)
    for i, x0 in enumerate(np.linspace(.10, .86, 5)):
        inset = ax.inset_axes([x0, .45, .10, .28]); inset.plot([1, 2, 3], [.51 + i * .01, .62 + i * .01, .71 + i * .01], "o-", color=PALETTE[0], lw=1.0, ms=2.5); inset.set_title("FP32", fontsize=5); inset.tick_params(labelsize=4); inset.grid(alpha=.25)
    fig.tight_layout(); _finish(fig, output)


def histogram_overlay(output: Path) -> None:
    rng = np.random.default_rng(14); fig, ax = plt.subplots(figsize=(6.6, 3.8)); bins = np.logspace(-2, 2, 32)
    for i, c in enumerate(PALETTE[:3]): ax.hist(10 ** rng.normal(-.1 + i * .35, .38, 1200), bins=bins, density=True, histtype="stepfilled", alpha=.25, color=c, label=f"Condition {i + 1}")
    ax.set_xscale("log"); ax.set_xlabel("Magnitude (log scale)"); ax.set_ylabel("Density"); ax.set_title("Overlaid distributions", loc="left", weight="bold"); ax.legend(frameon=False, fontsize=8); _style(ax); ax.grid(which="both", alpha=.22)
    ax.text(.98, .96, "n = 1,200 / group\nmedian shown by line", transform=ax.transAxes, ha="right", va="top", fontsize=8, bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "boxstyle": "round,pad=.35"})
    fig.tight_layout(); _finish(fig, output)


def architecture_schematic(output: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.0, 4.0)); ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    ax.add_patch(FancyBboxPatch((2.2, 3.15), 5.6, .55, boxstyle="round,pad=.03", facecolor="white", edgecolor="#334155")); ax.text(2.45, 3.43, "FP32 tensor", fontsize=8); ax.text(4.0, 3.43, "BF16 stored", fontsize=8, bbox={"facecolor": "#dbeafe", "edgecolor": "#6b8fc5", "linestyle": "--"}); ax.text(6.0, 3.43, "⇢ precision upcast", fontsize=8)
    boxes = [("$X_{in}$", .3, 1.6, 1.0, .7, "#fee2e2"), ("$QK^T$", 2.0, 2.1, 1.2, .65, "#dbeafe"), ("$A$", 4.0, 2.1, .8, .65, "#fee2e2"), ("$W_{up}$", 5.65, 2.1, 1.0, .65, "#dbeafe"), ("$W_{down}$", 7.25, 2.1, 1.2, .65, "#dbeafe"), ("$X_{out}$", 9.0, 1.6, .8, .7, "#fee2e2")]
    for label, x, y, w, h, c in boxes: ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=.04", facecolor=c, edgecolor="#334155", lw=1.1)); ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=9, weight="bold")
    for (_, x1, y1, w1, h1, _), (_, x2, y2, _, h2, _) in zip(boxes[:-1], boxes[1:]): ax.add_patch(FancyArrowPatch((x1 + w1, y1 + h1 / 2), (x2, y2 + h2 / 2), arrowstyle="-|>", mutation_scale=12, lw=1.2, color="#475569"))
    for x, label in [(1.1, "$W_Q$"), (1.1, "$W_K$"), (1.1, "$W_V$"), (6.15, "$W_{gate}$")]:
        y = 2.95 if label != "$W_V$" else 1.05; ax.add_patch(FancyBboxPatch((x, y), 1.0, .42, boxstyle="round,pad=.02", facecolor="#dbeafe", edgecolor="#6b8fc5", linestyle="--")); ax.text(x + .5, y + .21, label, ha="center", va="center", fontsize=7)
    ax.add_patch(FancyArrowPatch((1.2, 2.95), (2.4, 2.75), arrowstyle="-|>", mutation_scale=10, color="#6b8fc5")); ax.add_patch(FancyArrowPatch((1.2, 2.95), (2.4, 2.35), arrowstyle="-|>", mutation_scale=10, color="#6b8fc5")); ax.add_patch(FancyArrowPatch((1.2, 1.25), (2.4, 2.2), arrowstyle="-|>", mutation_scale=10, color="#6b8fc5")); ax.add_patch(FancyArrowPatch((3.0, 1.75), (7.7, 1.75), connectionstyle="arc3,rad=-.2", arrowstyle="-|>", mutation_scale=10, color=PALETTE[3])); ax.text(4.4, 1.22, "skip / residual path", fontsize=8, color=PALETTE[3])
    ax.text(.35, .35, "LayerCast-style tensor flow", fontsize=11, weight="bold"); ax.text(7.2, .35, "mixed precision state transitions", fontsize=8, color="#475569")
    _finish(fig, output)


def conceptual_multi_panel(output: Path) -> None:
    rng = np.random.default_rng(22); fig, axes = plt.subplots(2, 2, figsize=(7.4, 6.0))
    ax = axes[0, 0]; ax.axis("off"); ax.add_patch(Rectangle((.08, .35), .28, .28, fc="#dbeafe", ec="#334155")); ax.add_patch(Rectangle((.62, .35), .28, .28, fc="#dcfce7", ec="#334155")); ax.annotate("", (.62, .49), (.36, .49), arrowprops={"arrowstyle": "->", "lw": 1.5}); ax.text(.22, .49, "data", ha="center", va="center"); ax.text(.76, .49, "latent", ha="center", va="center"); ax.set_title("Architecture idea", loc="left", weight="bold", fontsize=9)
    ax = axes[0, 1]; pts = rng.normal(size=(80, 2)); ax.scatter(pts[:, 0], pts[:, 1], c=pts[:, 0] + pts[:, 1], cmap="viridis", s=16); ax.set_title("Latent space", loc="left", weight="bold", fontsize=9); _style(ax)
    ax = axes[1, 0]; mat = np.outer(np.sin(np.linspace(0, 2.8, 7)), np.cos(np.linspace(0, 2.8, 7))); ax.imshow(mat, cmap="PuBuGn", vmin=-1, vmax=1); ax.set_title("Interaction matrix", loc="left", weight="bold", fontsize=9); ax.set_xticks([]); ax.set_yticks([])
    ax = axes[1, 1]; ranks = np.arange(1, 40); ax.plot(ranks, 1 / ranks ** .7, color=PALETTE[0], lw=2); ax.scatter(ranks[::4], (1 / ranks ** .7)[::4], color=PALETTE[1], s=14); ax.set(xlabel="Rank", ylabel="Frequency"); ax.set_title("Rank summary", loc="left", weight="bold", fontsize=9); _style(ax)
    fig.tight_layout(); _finish(fig, output)


def scaling_two_panel(output: Path) -> None:
    rng = np.random.default_rng(31); fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.2))
    for i, ax in enumerate(axes):
        x = np.logspace(0, 2, 12); theory = .45 * x ** (.55 + i * .12); y = theory * np.exp(rng.normal(0, .06, len(x))); ax.errorbar(x, y, yerr=.08 * y, fmt="o", color=PALETTE[0], ms=4, capsize=2, label="data"); ax.plot(x, theory, color=PALETTE[1], lw=1.8, ls="--", label="theory"); ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("Parameter"); ax.set_ylabel("Response"); ax.set_title(["Theory vs data", "Exponent sweep"][i], loc="left", weight="bold", fontsize=9); ax.legend(frameon=False, fontsize=7); _style(ax)
    fig.tight_layout(); _finish(fig, output)


def scaling_five_panel(output: Path) -> None:
    rng = np.random.default_rng(35); fig = plt.figure(figsize=(11.0, 5.2)); gs = fig.add_gridspec(2, 6, hspace=.5, wspace=.6)
    axes = [fig.add_subplot(gs[0, 0:2]), fig.add_subplot(gs[0, 2:4]), fig.add_subplot(gs[0, 4:6]), fig.add_subplot(gs[1, 0:3]), fig.add_subplot(gs[1, 3:6])]
    x = np.arange(1, 9)
    axes[0].hist(rng.normal(0, 1, 500), bins=20, color=PALETTE[0], alpha=.75); axes[0].set_title("Distribution", fontsize=8, weight="bold")
    axes[1].loglog(x, 1 / x ** .7, "o-", color=PALETTE[1]); axes[1].set_title("Rank-frequency", fontsize=8, weight="bold")
    for i, c in enumerate(PALETTE[:3]): axes[2].plot(x, .3 + .07 * i + .05 * np.log(x), "o--", color=c, ms=3)
    axes[2].set_title("Variance / dimension", fontsize=8, weight="bold")
    axes[3].plot(x, .8 / x ** .55, "o-", color=PALETTE[3]); axes[3].plot(x, .8 / x ** .5, "--", color="#475569"); axes[3].set_title("Inverse scaling", fontsize=8, weight="bold")
    axes[4].errorbar(x, .25 + .08 * np.log(x), yerr=.03, fmt="o", color=PALETTE[4], capsize=2); axes[4].plot(x, .25 + .08 * np.log(x), ls="--", color=PALETTE[4], alpha=.5); axes[4].set_title("Exponent phase", fontsize=8, weight="bold")
    for ax in axes: _style(ax); ax.tick_params(labelsize=6)
    fig.tight_layout(w_pad=.9); _finish(fig, output)


RENDERERS: dict[str, Callable[[Path], None]] = {
    "6e0b081c34e20430": learning_curves,
    "43fe44adf197b97c": multi_panel_line_comparison,
    "227c2b8a31a21253": scatter_marginal,
    "1c6e9e67bade247d": mixed_statistics_grid,
    "a7a3dfa02b650b2e": mixed_multi_panel,
    "789156ffca30bef6": grouped_bar_inset,
    "7b7b02d82ccc7207": histogram_overlay,
    "60358c36e16732bf": architecture_schematic,
    "dcdd74bc2feb98d9": conceptual_multi_panel,
    "f5ca182539d043e4": scaling_two_panel,
    "653ce9637e303a41": scaling_five_panel,
}


def render_reference(reference_id: str, output: Path) -> None:
    try:
        renderer = RENDERERS[reference_id]
    except KeyError as exc:
        raise ValueError(f"No synthetic renderer registered for {reference_id}") from exc
    renderer(Path(output))
