#!/usr/bin/env python3
"""Generate the anti-pattern atlas: bad figure, diagnosis, corrected figure."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "assets" / "anti-pattern-atlas"


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def anti_pattern_dir(name: str) -> Path:
    d = ATLAS / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_in_dir(d: Path, code_bad: str, code_corrected: str) -> None:
    original_cwd = os.getcwd()
    os.chdir(d)
    try:
        exec(code_bad, {"plt": plt, "np": np})
        os.replace("figure.png", "bad.png")
        plt.close("all")
        exec(code_corrected, {"plt": plt, "np": np})
        os.replace("figure.png", "corrected.png")
        plt.close("all")
    finally:
        os.chdir(original_cwd)


def bar_hides_distribution() -> None:
    d = anti_pattern_dir("bar-hides-distribution")
    bad = '''\
import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(1)
data = [np.random.normal(0, 1, 8), np.random.normal(0.5, 1, 8)]
means = [np.mean(v) for v in data]
ax.bar([0, 1], means, color="#5b79a2")
ax.set_xticks([0, 1]); ax.set_xticklabels(["A", "B"])
ax.set_ylabel("Mean response")
fig.savefig("figure.png", dpi=150)
'''
    corrected = '''\
import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(1)
data = [np.random.normal(0, 1, 8), np.random.normal(0.5, 1, 8)]
positions = [1, 2]
parts = ax.violinplot(data, positions=positions, showmeans=True, showmedians=False)
for pc in parts['bodies']:
    pc.set_facecolor("#5b79a2"); pc.set_alpha(0.6)
ax.scatter(np.random.normal(1, 0.04, len(data[0])), data[0], color="#333333", s=20, zorder=3)
ax.scatter(np.random.normal(2, 0.04, len(data[1])), data[1], color="#333333", s=20, zorder=3)
ax.set_xticks(positions); ax.set_xticklabels(["A", "B"])
ax.set_ylabel("Response")
fig.savefig("figure.png", dpi=150)
'''
    run_in_dir(d, bad, corrected)
    write_json(d / "metadata.json", {
        "rule_ids": ["STAT-005"],
        "family": "comparison_effect",
        "source_ids": ["weissgerber-2015", "plos-data-presentation"],
    })
    (d / "diagnosis.md").write_text(
        "# Bar hides distribution\n\n"
        "**Bad:** mean-only bars for small-sample continuous data.\n\n"
        "**Why it fails:** STAT-005 requires individual observations or distribution marks.\n\n"
        "**Corrected:** violin plot plus individual points.\n",
        encoding="utf-8",
    )


def rainbow_heatmap() -> None:
    d = anti_pattern_dir("rainbow-heatmap")
    bad = '''\
import numpy as np
fig, ax = plt.subplots(figsize=(4, 3.5))
data = np.random.rand(10, 10)
im = ax.imshow(data, cmap="jet")
fig.colorbar(im, ax=ax)
ax.set_title("Rainbow heatmap")
fig.savefig("figure.png", dpi=150)
'''
    corrected = '''\
import numpy as np
fig, ax = plt.subplots(figsize=(4, 3.5))
data = np.random.rand(10, 10)
im = ax.imshow(data, cmap="viridis")
fig.colorbar(im, ax=ax)
ax.set_title("Perceptually uniform heatmap")
fig.savefig("figure.png", dpi=150)
'''
    run_in_dir(d, bad, corrected)
    write_json(d / "metadata.json", {
        "rule_ids": ["HOUSE-009", "A11Y-001"],
        "family": "matrix_array",
        "source_ids": ["crameri-2020"],
    })
    (d / "diagnosis.md").write_text(
        "# Rainbow heatmap\n\n"
        "**Bad:** jet/rainbow colormap for sequential quantitative data.\n\n"
        "**Why it fails:** HOUSE-009 requires perceptually uniform colormaps; A11Y-001 is violated when hue alone encodes magnitude.\n\n"
        "**Corrected:** viridis or another perceptually uniform sequential colormap.\n",
        encoding="utf-8",
    )


def roc_only_model_comparison() -> None:
    d = anti_pattern_dir("roc-only-model-comparison")
    bad = '''\
import numpy as np
fig, ax = plt.subplots(figsize=(4, 4))
n = 2000
labels = np.random.binomial(1, 0.3, n)
scores = np.where(labels, np.random.beta(7, 3, n), np.random.beta(3, 7, n))
order = np.argsort(scores)[::-1]
tpr = np.cumsum(labels[order]) / max(1, labels.sum())
fpr = np.cumsum(1 - labels[order]) / max(1, (1 - labels).sum())
auc = np.trapezoid(tpr, fpr)
ax.plot(fpr, tpr, color="#5b79a2", linewidth=2, label=f"AUC = {auc:.2f}")
ax.plot([0, 1], [0, 1], "k--", linewidth=1)
ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
ax.set_title("ROC only")
ax.legend()
fig.savefig("figure.png", dpi=150)
'''
    corrected = '''\
import numpy as np
fig, axes = plt.subplots(1, 2, figsize=(8, 4))
n = 2000
labels = np.random.binomial(1, 0.3, n)
scores = np.where(labels, np.random.beta(7, 3, n), np.random.beta(3, 7, n))
order = np.argsort(scores)[::-1]
tpr = np.cumsum(labels[order]) / max(1, labels.sum())
fpr = np.cumsum(1 - labels[order]) / max(1, (1 - labels).sum())
axes[0].plot(fpr, tpr, color="#5b79a2", linewidth=2)
axes[0].plot([0, 1], [0, 1], "k--", linewidth=1)
axes[0].set_title("ROC (discrimination)")
axes[0].set_xlabel("FPR"); axes[0].set_ylabel("TPR")
# calibration
bins = np.linspace(0, 1, 6)
bin_idx = np.digitize(scores, bins[1:-1])
mean_pred = np.array([scores[bin_idx == i].mean() for i in range(len(bins)-1)])
mean_obs = np.array([labels[bin_idx == i].mean() for i in range(len(bins)-1)])
axes[1].plot([0, 1], [0, 1], "k--", linewidth=1)
axes[1].plot(mean_pred, mean_obs, "o-", color="#6baf72")
axes[1].set_title("Calibration (probability quality)")
axes[1].set_xlabel("Mean predicted"); axes[1].set_ylabel("Observed fraction")
fig.tight_layout()
fig.savefig("figure.png", dpi=150)
'''
    run_in_dir(d, bad, corrected)
    write_json(d / "metadata.json", {
        "rule_ids": ["CLF-001"],
        "family": "classification_diagnostics",
        "source_ids": ["tripod-ai"],
    })
    (d / "diagnosis.md").write_text(
        "# ROC-only model comparison\n\n"
        "**Bad:** only ROC/AUC is shown.\n\n"
        "**Why it fails:** CLF-001 states that discrimination, calibration, and threshold utility are separate claims.\n\n"
        "**Corrected:** add a calibration panel.\n",
        encoding="utf-8",
    )


def categorical_points_connected() -> None:
    d = anti_pattern_dir("categorical-points-connected")
    bad = '''\
import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(3)
x = np.arange(3)
y = np.random.uniform(0.4, 0.8, 3)
ax.plot(x, y, "o-", color="#5b79a2", linewidth=2, markersize=8)
ax.set_xticks(x); ax.set_xticklabels(["A", "B", "C"])
ax.set_ylabel("Score")
fig.savefig("figure.png", dpi=150)
'''
    corrected = '''\
import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(3)
x = np.arange(3)
y = np.random.uniform(0.4, 0.8, 3)
ax.scatter(x, y, color="#5b79a2", s=80, zorder=3)
ax.set_xticks(x); ax.set_xticklabels(["A", "B", "C"])
ax.set_ylabel("Score")
ax.set_title("Categorical operating points")
fig.savefig("figure.png", dpi=150)
'''
    run_in_dir(d, bad, corrected)
    write_json(d / "metadata.json", {
        "rule_ids": ["PAIR-002", "SEM-002"],
        "family": "paired_operating_point",
        "source_ids": ["pfd-family-guidance", "heer-bostock-2010"],
    })
    (d / "diagnosis.md").write_text(
        "# Categorical points connected as line\n\n"
        "**Bad:** unordered categorical operating points connected by a trajectory.\n\n"
        "**Why it fails:** PAIR-002 and SEM-002 prohibit implying continuity where none exists.\n\n"
        "**Corrected:** use points only.\n",
        encoding="utf-8",
    )


def oversized_legend() -> None:
    d = anti_pattern_dir("oversized-legend")
    bad = '''\
import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(5)
x = np.linspace(0, 1, 50)
for i in range(4):
    ax.plot(x, np.sin(x * np.pi + i * 0.2), label=f"Series {i+1}")
ax.legend(loc="upper right", fontsize=14)
ax.set_xlim(0, 1); ax.set_ylim(0, 1.5)
fig.savefig("figure.png", dpi=150)
'''
    corrected = '''\
import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(5)
x = np.linspace(0, 1, 50)
for i in range(4):
    ax.plot(x, np.sin(x * np.pi + i * 0.2), label=f"S{i+1}")
ax.legend(loc="upper right", fontsize=8, frameon=False)
ax.set_xlim(0, 1); ax.set_ylim(0, 1.5)
fig.savefig("figure.png", dpi=150)
'''
    run_in_dir(d, bad, corrected)
    write_json(d / "metadata.json", {
        "rule_ids": ["LAY-002", "ANN-002"],
        "family": "curve_comparison",
        "source_ids": ["pfd-render-trace"],
    })
    (d / "diagnosis.md").write_text(
        "# Oversized legend\n\n"
        "**Bad:** large legend crowds data area.\n\n"
        "**Why it fails:** LAY-002 requires clearance; ANN-002 asks for compact legends.\n\n"
        "**Corrected:** smaller font, shorter labels, frame removed.\n",
        encoding="utf-8",
    )


def equal_sized_panels() -> None:
    d = anti_pattern_dir("equal-sized-panels")
    bad = '''\
import numpy as np
fig, axes = plt.subplots(2, 2, figsize=(6, 6))
for ax in axes.flat:
    ax.plot([0, 1], [0, 1])
    ax.set_title("Panel")
fig.tight_layout()
fig.savefig("figure.png", dpi=150)
'''
    corrected = '''\
import numpy as np
fig = plt.figure(figsize=(8, 5))
gs = fig.add_gridspec(2, 2, width_ratios=[2, 1], height_ratios=[2, 1])
ax_hero = fig.add_subplot(gs[0, 0])
ax_hero.plot([0, 1], [0, 1])
ax_hero.set_title("Main evidence")
for idx in [(0, 1), (1, 0), (1, 1)]:
    ax = fig.add_subplot(gs[idx])
    ax.plot([0, 1], [0, 1])
    ax.set_title("Support")
fig.tight_layout()
fig.savefig("figure.png", dpi=150)
'''
    run_in_dir(d, bad, corrected)
    write_json(d / "metadata.json", {
        "rule_ids": ["LAY-003"],
        "family": "asymmetric_multi_panel",
        "source_ids": ["pfd-house-visual-language"],
    })
    (d / "diagnosis.md").write_text(
        "# Equal-sized panels\n\n"
        "**Bad:** no visual hierarchy; all panels same size.\n\n"
        "**Why it fails:** LAY-003 says visual mass should match evidence importance.\n\n"
        "**Corrected:** hero panel with supporting smaller panels.\n",
        encoding="utf-8",
    )


PATTERNS = [
    bar_hides_distribution,
    rainbow_heatmap,
    roc_only_model_comparison,
    categorical_points_connected,
    oversized_legend,
    equal_sized_panels,
]


def main() -> int:
    ATLAS.mkdir(parents=True, exist_ok=True)
    for pattern in PATTERNS:
        pattern()
    print(json.dumps({"generated": len(PATTERNS)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
