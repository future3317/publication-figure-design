#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(4, 3), facecolor="#eeeeee")
ax.set_facecolor("#eeeeee")
ax.plot([0, 1], [0, 1], color="#aaaaaa")
ax.text(0.5, 0.5, "Low contrast label", color="#bbbbbb", ha="center", fontsize=10)
ax.set_xlabel("x", color="#aaaaaa")
ax.set_ylabel("y", color="#aaaaaa")
fig.savefig("figure.png", dpi=150)

