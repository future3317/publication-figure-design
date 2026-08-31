#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(8, 3))
axes[0].plot([0, 1], [0, 1])
axes[0].set_xlim(0, 1)
axes[0].set_ylim(0, 1)
axes[0].set_title("Panel A")
axes[1].plot([0, 1], [0, 2])
axes[1].set_xlim(0, 1)
axes[1].set_ylim(0, 2)
axes[1].set_title("Panel B")
fig.savefig("figure.png", dpi=150)

