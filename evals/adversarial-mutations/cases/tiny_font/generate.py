#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(2, 2))
ax.plot([0, 1], [0, 1])
ax.set_xlabel("x", fontsize=4)
ax.set_ylabel("y", fontsize=4)
ax.tick_params(axis="both", labelsize=4)
ax.set_title("Tiny font mutation", fontsize=5)
fig.savefig("figure.png", dpi=300)

