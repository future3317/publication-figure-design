import matplotlib.pyplot as plt
import numpy as np

matrix = np.array([[85, 12], [18, 65]], dtype=float)
normalized = matrix / matrix.sum(axis=1, keepdims=True)
fig, ax = plt.subplots(figsize=(4, 4))
im = ax.imshow(normalized, cmap="Blues", vmin=0, vmax=1)
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{normalized[i, j]:.2f}", ha="center", va="center", fontsize=14, color="white" if normalized[i, j] > 0.5 else "black")
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(["Pred 0", "Pred 1"])
ax.set_yticklabels(["True 0", "True 1"])
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("Confusion matrix (normalized by row)")
fig.colorbar(im, ax=ax, label="Fraction")
fig.tight_layout()
fig.savefig("image.png", dpi=150)
