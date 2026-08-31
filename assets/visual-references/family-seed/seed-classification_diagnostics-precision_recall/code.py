import matplotlib.pyplot as plt
import numpy as np

np.random.seed(29)
n = 2000
labels = np.random.binomial(1, 0.2, n)
scores = np.where(labels, np.random.beta(7, 3, n), np.random.beta(2, 8, n))
order = np.argsort(scores)[::-1]
labels_sorted = labels[order]
precision = np.cumsum(labels_sorted) / np.arange(1, n + 1)
recall = np.cumsum(labels_sorted) / max(1, labels.sum())
baseline = labels.mean()

fig, ax = plt.subplots(figsize=(4, 4))
ax.plot(recall, precision, color="#6baf72", linewidth=2, label="Model")
ax.axhline(baseline, color="#9e9e9e", linestyle="--", linewidth=1, label=f"Baseline = {baseline:.2f}")
ax.set_xlabel("Recall")
ax.set_ylabel("Precision")
ax.set_title("Precision-recall curve")
ax.legend(loc="lower left", fontsize=8)
fig.tight_layout()
fig.savefig("image.png", dpi=150)
