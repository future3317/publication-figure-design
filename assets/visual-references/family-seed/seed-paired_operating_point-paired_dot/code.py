import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
n = 18
conditions = ["A", "B", "C"]
x = np.arange(len(conditions))
# paired observations
base = np.random.uniform(0.4, 0.7, n)
effect = np.array([0.0, 0.15, -0.05]) + np.random.normal(0, 0.03, (n, 3))
y = base[:, None] + effect

fig, ax = plt.subplots(figsize=(4, 4))
for i in range(n):
    ax.plot(x, y[i], "o-", color="#9e9e9e", alpha=0.4, linewidth=0.8, markersize=4)
ax.set_xticks(x)
ax.set_xticklabels(conditions)
ax.set_ylabel("Response")
ax.set_title("Paired observations at three operating points")
fig.tight_layout()
fig.savefig("image.png", dpi=150)
