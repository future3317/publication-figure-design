# Color Palette Reference

> **BASELINE -- COPY VERBATIM:** Copy this block into every generated script. Do not modify values, omit lines, or substitute default palettes.

```python
# Academic Figure Skill Nature/Cell/Science Color Palette -- COPY VERBATIM
CATEGORICAL = ["#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666"]
CATEGORICAL_EXTENDED = [
    "#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666",
    "#4393C3", "#D6604D", "#5AAE61", "#B35806", "#9970AB", "#999999",
]
DIVERGING   = ["#2166AC", "#F7F7F7", "#B2182B"]
SEQUENTIAL  = ["#F7FBFF", "#6BAED6", "#08306B"]
ACCENT_RED  = "#B2182B"
GREY        = "#999999"
BLACK       = "#222222"
```

```r
# Academic Figure Skill Nature/Cell/Science Color Palette -- COPY VERBATIM
categorical <- c("#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666")
categorical_extended <- c(
  "#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666",
  "#4393C3", "#D6604D", "#5AAE61", "#B35806", "#9970AB", "#999999"
)
diverging  <- c("#2166AC", "#F7F7F7", "#B2182B")
sequential <- c("#F7FBFF", "#6BAED6", "#08306B")
accent_red <- "#B2182B"
grey       <- "#999999"
black      <- "#222222"
```

---

## Nature / Cell / Science Color Rules

Academic Figure Skill uses a restrained journal-safe palette rather than default matplotlib, ggplot2, seaborn, Excel, Scanpy, or rainbow palettes. The target look is: high contrast, print-safe, colorblind-aware, and semantically assigned.

### 1. Use Semantic Roles

- Blue `#2166AC`: primary reference, control, baseline, or negative direction.
- Red `#B2182B`: strongest emphasis, disease/high-risk/up-regulated direction; use sparingly.
- Green `#1B7837`: treatment, recovery, beneficial, or orthogonal biological group.
- Orange `#F1A340`: secondary contrast when red is already reserved for emphasis.
- Purple `#762A83`: third/fourth category, model family, or alternate lineage.
- Grey `#999999`: background, non-significant, other, or low-priority category.

### 2. Limit Saturated Color Area

Use 2-4 main colors plus one accent. The accent color should occupy a small area: selected labels, threshold highlights, top genes, or a single hero result. Large saturated red blocks make the figure feel alarmist and are harder to read in print.

### 3. Avoid Red-Green-Only Encoding

Red and green may both appear in the palette, but they must not be the only cue for a critical comparison. Add at least one redundant encoding: shape, line style, direct label, facet, or ordering.

### 4. Match Palette to Data Type

- Categorical data: use `CATEGORICAL` up to six classes.
- More than six classes: use `CATEGORICAL_EXTENDED`, then add direct labels or grouping; avoid legends with 12+ tiny entries when possible.
- Diverging data such as log2FC, z-score, signed correlations: use `DIVERGING` centered at the scientific zero.
- Sequential data such as expression, density, abundance, confidence: use `SEQUENTIAL` or a perceptually uniform single-hue map.
- Non-significant or background points: use grey with low alpha, plotted below signal layers.

### 5. Never Use These Palettes

Reject `jet`, `rainbow`, `hsv`, `tab10`, `tab20`, seaborn `deep/muted/pastel/bright/dark/colorblind`, ggplot2 hue defaults, Excel defaults, and Brewer qualitative `Set1/Set2/Set3/Paired` as final journal palettes. They look default, can distort luminance, or become crowded in multi-panel figures.

### 6. Multi-Panel Consistency

A color means the same thing across all panels in one figure. If blue means control in panel a, blue cannot mean treatment in panel d. Reserve red for the single strongest result or risk direction across the whole figure.

## Quick Use

**Python**
```python
colors = CATEGORICAL[:n_groups]
ax.plot(x, y, color=CATEGORICAL[0])
ax.scatter(x_ns, y_ns, color=GREY, alpha=0.25)
```

**R**
```r
scale_color_manual(values = categorical[seq_len(n_groups)])
scale_fill_gradientn(colors = diverging)
```

---

## Optional: Unified Categorical Palette Manager

For figures that need a softer, non-journal-default look, the skill also provides a
standalone categorical palette manager in `scripts/palette_manager.py`. It is kept
separate from the baseline above so existing scripts are not affected.

### Built-in palettes

| ID | Chinese name | Tags |
|----|--------------|------|
| `pastel_girl` | 粉彩少女 | pastel, soft, pink, purple |
| `sweet_macaron` | 甜蜜马卡龙 | macaron, pastel, bright |
| `soft_forest` | 柔绿森林 | forest, green, muted |
| `blue_green_land` | 蓝天绿地 | blue, green, contrast |
| `watercolor_bloom` | 水色花影 | watercolor, teal, purple |
| `fresh_holiday` | 清新假日 | fresh, green, blue, orange |
| `summer_beach` | 夏日海滩 | summer, coral, orange, blue |

Each palette contains 8 hex colors and is intended for **categorical / qualitative**
use only. Do not use it as a continuous colormap.

### Python API

```python
from scripts.palette_manager import (
    list_palettes, get_palette, resolve_palette,
    set_default_palette, resolve_colors, preview_palettes
)

# list all palettes
list_palettes()

# get colors by id or Chinese name
get_palette("summer_beach")
get_palette("夏日海滩", n=5)

# set task-wide default and resolve it
set_default_palette("soft_forest")
colors = resolve_palette(n=4)  # uses default

# explicit colors > explicit palette > default
colors = resolve_colors(
    colors=["#FF0000", "#00FF00"],  # wins if provided
    palette="summer_beach",
    n=4,
)

# preview all palettes
fig = preview_palettes()
fig.savefig("palette_preview.png", dpi=300)
```

### Rules of thumb

1. **Categorical only** — scatter, bar, boxplot, violin, line, area, stacked bar, etc.
2. **Stable mapping** — assign categories to palette indices in a deterministic order
   (e.g., sorted category names) so colors stay consistent across panels.
3. **Subset by index** — when `n <= 8`, `get_palette` returns the first `n` colors in
   fixed order; no random sampling.
4. **Extension by interpolation** — when `n > 8`, the original 8 colors are preserved
   and supplementary colors are generated by HSL interpolation.
5. **Never override explicit colors** — if the user supplies colors, use them directly.
6. **Palette ≠ theme** — figure background, panel background, grid, axis, and text
   styling remain independent of the palette choice.
