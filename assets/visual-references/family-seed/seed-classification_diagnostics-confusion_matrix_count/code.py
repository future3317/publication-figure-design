import matplotlib.pyplot as plt
import numpy as np

matrix = np.array([[85, 12], [18, 65]])
fig, ax = plt.subplots(figsize=(4, 4))
im = ax.imshow(matrix, cmap="Blues")
for i in range(2):
    for j in range(2):
        ax.text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=14, color="white" if matrix[i, j] > 50 else "black")
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(["Pred 0", "Pred 1"])
ax.set_yticklabels(["True 0", "True 1"])
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("Confusion matrix (counts)")
fig.colorbar(im, ax=ax, label="Count")
fig.tight_layout()
fig.savefig("image.png", dpi=150)
