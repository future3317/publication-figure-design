import matplotlib.pyplot as plt
import numpy as np

np.random.seed(37)
n = 2000
labels = np.random.binomial(1, 0.3, n)
scores = np.where(labels, np.random.beta(7, 3, n), np.random.beta(3, 7, n))
thresholds = np.linspace(0, 1, 100)
precision = []
recall = []
for t in thresholds:
    pred = (scores >= t).astype(int)
    tp = int(((pred == 1) & (labels == 1)).sum())
    fp = int(((pred == 1) & (labels == 0)).sum())
    fn = int(((pred == 0) & (labels == 1)).sum())
    precision.append(tp / max(1, tp + fp))
    recall.append(tp / max(1, tp + fn))

fig, ax = plt.subplots(figsize=(5, 4))
ax.plot(thresholds, precision, color="#5b79a2", linewidth=2, label="Precision")
ax.plot(thresholds, recall, color="#6baf72", linewidth=2, label="Recall")
ax.axvline(0.5, color="#c75b6b", linestyle="--", linewidth=1.5, label="Selected threshold")
ax.set_xlabel("Threshold")
ax.set_ylabel("Metric value")
ax.set_title("Threshold trade-off curve")
ax.legend(loc="center right", fontsize=8)
fig.tight_layout()
fig.savefig("image.png", dpi=150)
