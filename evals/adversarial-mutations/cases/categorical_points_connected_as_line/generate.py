#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(3)
x = np.arange(3)
y = np.random.uniform(0.4, 0.8, 3)
ax.plot(x, y, "o-", color="#5b79a2", linewidth=2, markersize=8)
ax.set_xticks(x)
ax.set_xticklabels(["Method A", "Method B", "Method C"])
ax.set_ylabel("Score")
fig.savefig("figure.png", dpi=150)

