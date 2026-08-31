import matplotlib.pyplot as plt
import numpy as np

np.random.seed(11)
n = 24
x1 = np.random.normal(0.5, 0.1, n)
x2 = x1 + np.random.normal(0.1, 0.06, n)

fig, ax = plt.subplots(figsize=(4, 4))
ax.scatter(x1, x2, color="#5b79a2", s=40, alpha=0.7)
for a, b in zip(x1, x2):
    ax.plot([a, b], [b, a], color="#9e9e9e", linewidth=0.5, alpha=0.3)
ax.plot([0.2, 0.8], [0.2, 0.8], "k--", linewidth=1, label="y=x")
ax.set_xlabel("Method X")
ax.set_ylabel("Method Y")
ax.set_title("Connected paired observations")
ax.legend()
fig.tight_layout()
fig.savefig("image.png", dpi=150)
