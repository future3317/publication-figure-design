#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(4, 3))
ax.plot([0, 1, 2], [0.2, 0.5, 0.3])
ax.set_xlabel("Time")
ax.set_ylabel("Concentration")
fig.savefig("figure.png", dpi=150)

