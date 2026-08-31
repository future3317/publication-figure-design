#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import numpy as np
fig, ax = plt.subplots(figsize=(4, 3))
np.random.seed(5)
x = np.linspace(0, 1, 50)
for i in range(4):
    ax.plot(x, np.sin(x * np.pi + i * 0.2), label=f"Series {i+1}")
ax.legend(loc="upper right", fontsize=14)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1.5)
fig.savefig("figure.png", dpi=150)

