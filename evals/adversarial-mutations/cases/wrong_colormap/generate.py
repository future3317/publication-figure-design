#!/usr/bin/env python3
"""Generate the mutated figure for eval."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import numpy as np
fig, ax = plt.subplots(figsize=(4, 3.5))
data = np.random.rand(10, 10)
im = ax.imshow(data, cmap="jet")
fig.colorbar(im, ax=ax)
ax.set_title("Sequential data with rainbow colormap")
fig.savefig("figure.png", dpi=150)

