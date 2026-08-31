#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
x = np.arange(3)
y = np.array([1.0, 1.2, 0.9])
sem = np.array([0.05, 0.06, 0.04])
ax.bar(x, y, yerr=sem, capsize=4, color="#5b79a2")
ax.set_xticks(x)
ax.set_xticklabels(["A", "B", "C"])
ax.set_ylabel("Mean (SD)")
fig.savefig("figure.png", dpi=150)

