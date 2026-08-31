import matplotlib.pyplot as plt
import numpy as np

np.random.seed(19)
n = 20
before = np.random.uniform(0.4, 0.8, n)
delta = np.random.normal(0.12, 0.08, n)

fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(before, delta, color="#5b79a2", s=50, alpha=0.7)
ax.axhline(0, color="#333333", linewidth=1)
ax.set_xlabel("Before score")
ax.set_ylabel("Change (After - Before)")
ax.set_title("Before-after effect estimates")
fig.tight_layout()
fig.savefig("image.png", dpi=150)
