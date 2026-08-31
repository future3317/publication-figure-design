#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(2)
before = np.random.uniform(0.3, 0.7, 12)
after = before + np.random.normal(0.1, 0.05, 12)
ax.bar([0, 1], [before.mean(), after.mean()], color=["#5b79a2", "#6baf72"])
ax.set_xticks([0, 1])
ax.set_xticklabels(["Before", "After"])
ax.set_ylabel("Mean score")
fig.savefig("figure.png", dpi=150)

