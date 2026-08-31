#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(4)
for i, label in enumerate(["A", "B", "C"]):
    x = np.random.normal(i, 0.1, 20)
    y = np.random.normal(i, 0.1, 20)
    ax.scatter(x, y, color=plt.cm.tab10(i), label=label)
ax.legend()
fig.savefig("figure.png", dpi=150)

