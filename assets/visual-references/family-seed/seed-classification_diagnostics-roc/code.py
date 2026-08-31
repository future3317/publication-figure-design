import matplotlib.pyplot as plt
import numpy as np

np.random.seed(23)
n = 2000
labels = np.random.binomial(1, 0.3, n)
scores = np.where(labels, np.random.beta(7, 3, n), np.random.beta(3, 7, n))
order = np.argsort(scores)[::-1]
labels_sorted = labels[order]
tpr = np.cumsum(labels_sorted) / max(1, labels.sum())
fpr = np.cumsum(1 - labels_sorted) / max(1, (1 - labels).sum())
auc = np.trapezoid(tpr, fpr)

fig, ax = plt.subplots(figsize=(4, 4))
ax.plot(fpr, tpr, color="#5b79a2", linewidth=2, label=f"AUC = {auc:.2f}")
ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Chance")
ax.scatter([0.2], [0.72], color="#c75b6b", s=60, zorder=3, label="Operating point")
ax.set_xlabel("False positive rate")
ax.set_ylabel("True positive rate")
ax.set_title("ROC curve with operating point")
ax.legend(loc="lower right", fontsize=8)
fig.tight_layout()
fig.savefig("image.png", dpi=150)
