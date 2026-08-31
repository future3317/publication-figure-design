import matplotlib.pyplot as plt
import numpy as np

np.random.seed(7)
n = 12
before = np.random.uniform(0.3, 0.9, n)
after = before + np.random.normal(0.12, 0.08, n)
y = np.arange(n)

fig, ax = plt.subplots(figsize=(5, 5))
ax.hlines(y, before, after, color="#5b79a2", linewidth=2, alpha=0.7)
ax.scatter(before, y, color="#c75b6b", s=50, label="Before", zorder=3)
ax.scatter(after, y, color="#6baf72", s=50, label="After", zorder=3)
ax.set_yticks([])
ax.set_xlabel("Score")
ax.set_title("Dumbbell plot: matched before/after pairs")
ax.legend()
fig.tight_layout()
fig.savefig("image.png", dpi=150)
