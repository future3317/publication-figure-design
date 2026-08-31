import matplotlib.pyplot as plt
import numpy as np

np.random.seed(3)
items = [f"M{i}" for i in range(1, 9)]
before = np.random.uniform(0.2, 0.8, len(items))
after = before + np.random.normal(0.1, 0.15, len(items))

fig, ax = plt.subplots(figsize=(4, 5))
for i, item in enumerate(items):
    color = "#6baf72" if after[i] > before[i] else "#c75b6b"
    ax.plot([0, 1], [before[i], after[i]], "o-", color=color, linewidth=1.5, markersize=5)
    ax.text(-0.05, before[i], item, ha="right", va="center", fontsize=7)
    ax.text(1.05, after[i], f"{after[i]:.2f}", ha="left", va="center", fontsize=7)
ax.set_xticks([0, 1])
ax.set_xticklabels(["Before", "After"])
ax.set_ylabel("Score")
ax.set_title("Slopegraph: paired change")
ax.set_xlim(-0.2, 1.2)
fig.tight_layout()
fig.savefig("image.png", dpi=150)
