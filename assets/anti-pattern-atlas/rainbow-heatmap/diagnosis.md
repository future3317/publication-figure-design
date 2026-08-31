# Rainbow heatmap

**Bad:** jet/rainbow colormap for sequential quantitative data.

**Why it fails:** HOUSE-009 requires perceptually uniform colormaps; A11Y-001 is violated when hue alone encodes magnitude.

**Corrected:** viridis or another perceptually uniform sequential colormap.
