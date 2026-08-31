#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(4, 3))
ax.plot([0, 1], [0, 1])
ax.text(1.02, 1.02, "Out", fontsize=12, color="#c75b6b")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
fig.savefig("figure.png", dpi=150, bbox_inches="tight")

