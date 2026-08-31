#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(1)
data = [np.random.normal(0, 1, 8), np.random.normal(0.5, 1, 8)]
means = [np.mean(v) for v in data]
ax.bar([0, 1], means, color="#5b79a2")
ax.set_xticks([0, 1])
ax.set_xticklabels(["A", "B"])
ax.set_ylabel("Mean response")
fig.savefig("figure.png", dpi=150)

