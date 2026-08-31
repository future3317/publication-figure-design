import matplotlib.pyplot as plt
import numpy as np

np.random.seed(31)
n = 1500
labels = np.random.binomial(1, 0.3, n)
probs = np.clip(np.where(labels, np.random.beta(5, 2, n), np.random.beta(2, 5, n)), 0.001, 0.999)

n_bins = 5
bin_edges = np.linspace(0, 1, n_bins + 1)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_indices = np.digitize(probs, bin_edges[1:-1])
mean_pred = np.array([probs[bin_indices == i].mean() for i in range(n_bins)])
mean_obs = np.array([labels[bin_indices == i].mean() for i in range(n_bins)])

fig, ax = plt.subplots(figsize=(4, 4))
ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Perfectly calibrated")
ax.plot(mean_pred, mean_obs, "o-", color="#5b79a2", linewidth=2, markersize=6, label="Model")
for i, c in enumerate(bin_centers):
    count = int((bin_indices == i).sum())
    ax.text(mean_pred[i], mean_obs[i] + 0.04, f"n={count}", ha="center", fontsize=7)
ax.set_xlabel("Mean predicted probability")
ax.set_ylabel("Fraction of positives")
ax.set_title("Calibration diagram")
ax.legend(loc="upper left", fontsize=8)
fig.tight_layout()
fig.savefig("image.png", dpi=150)
