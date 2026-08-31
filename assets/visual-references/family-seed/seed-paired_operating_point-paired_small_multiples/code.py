import matplotlib.pyplot as plt
import numpy as np

np.random.seed(5)
fig, axes = plt.subplots(1, 3, figsize=(9, 3), sharey=True)
conditions = ["A", "B", "C"]
for idx, ax in enumerate(axes):
    before = np.random.uniform(0.3, 0.7, 10)
    after = before + np.random.normal(0.08, 0.05, 10)
    for b, a in zip(before, after):
        ax.plot([0, 1], [b, a], "o-", color="#5b79a2", alpha=0.6, markersize=4)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Pre", "Post"])
    ax.set_title(conditions[idx])
axes[0].set_ylabel("Score")
fig.suptitle("Paired small multiples")
fig.tight_layout()
fig.savefig("image.png", dpi=150)
