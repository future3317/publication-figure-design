# Publication Style Patterns

> Design patterns derived from the `figures4papers` house style, migrated from
> the `scientific-figure-making` skill. Use these for matplotlib figures that
> need a clean, publication-ready look.

## When to load this file

- Building bar comparisons, trend panels, heatmaps, or multi-panel layouts in
  matplotlib.
- You want print-safe encodings that survive grayscale conversion.
- You need consistent semantic color roles across related figures.

## 1. Ultra-wide aspect for multi-metric panels

When comparing 3-4 metrics or many categories in a single row, use a wide
canvas so bars and labels do not crowd vertically.

- **Typical sizes:** `figsize=(45, 12)` for very large comparison panels, or
  `(28, 6)` for moderate multi-metric rows.
- **Rule of thumb:** width is often 3-4× height for comparison bars.
- **Why:** Readers scan left-to-right; wide panels keep y-axis labels and
  legends readable.

## 2. Dedicated legend panel

When multiple curves or groups make the legend large, place it in its own
subplot so it does not cover data.

```python
# Last axis reserved for legend only
axes[-1].set_axis_off()
handles, labels = axes[0].get_legend_handles_labels()
axes[-1].legend(handles, labels, loc="center", frameon=False)
```

**Result:** Data panels stay clean and the legend is fully visible.

## 3. Categorical bars without x-tick labels

When the x-axis is "method" or "condition" and the legend already identifies
them, hide x ticks and rely on the legend or panel title.

```python
ax.set_xticks([])
# or
ax.set_xticklabels([])
```

**Use when:** many methods are compared across multiple metrics; names are in
the legend or panel title.

## 4. Dynamic y-axis scaling

Tighten y-limits to the relevant range so differences are visible instead of
squashed.

```python
margin = 0.05 * (data.max() - data.min())
ax.set_ylim(data.min() - margin, data.max() + margin)
```

**Avoid:** fixed 0-100 when all values sit in 85-95; use 80-100 instead.

## 5. Print-safe bar separation

Bars that differ only by fill color can blur in grayscale. Add edges and,
when needed, hatching.

```python
ax.bar(x, height, color=color, edgecolor="black", linewidth=1.5)
# For grayscale-safe subgroups
ax.bar(x, height, color=color, hatch="/", edgecolor="black")
```

- **Edges:** `edgecolor="black"`, `linewidth=1.5-3` for clear separation.
- **Hatch:** `/`, `\`, `.` for ablation or subgroups.

## 6. Semantic color roles

Use a consistent semantic palette so "proposed vs baseline" reads the same way
across figures.

| Role | Suggested color | Usage |
|---|---|---|
| Proposed / key method | `#0F4D92` or `#3775BA` | The result you want to highlight |
| Improvement / positive | `#8BCF8B` or `#AADCA9` | Gains, recoveries, beneficial variants |
| Baseline / contrast | `#B64342` or `#E9A6A1` | Alternatives, controls, negative direction |
| Neutral / background | `#CFCECE` or `#767676` | Reference or low-priority categories |
| Highlight / callout | `#FFD700` | A single callout only |

## 7. Alpha-based ablation encoding

For ablation studies, use the same primary color with varying alpha levels
(0.2 to 1.0) to represent the "completeness" of a method.

```python
alphas = np.linspace(0.2, 1.0, len(ablation_conditions))
for cond, alpha in zip(conditions, alphas):
    ax.bar(..., color=blue_main, alpha=alpha, edgecolor="black")
```

## 8. Direct bar annotation

Print values directly above bars so exact numbers are readable without a grid.

```python
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height,
            f"{height:.2f}", ha="center", va="bottom", fontsize=10)
```

Use large fonts (relative to panel size) for big comparison bars.

## Relationship to existing references

- Typography defaults remain in `references/typography.md`.
- Color palettes and the categorical palette manager remain in
  `references/color-palettes.md`.
- Export formats and DPI remain in `references/export-specs.md`.
- Multi-panel narrative principles remain in `references/multipanel-layout.md`.

This file adds layout and encoding conventions that complement those baselines.

## Source

Patterns derived from the
[figures4papers](https://github.com/ChenLiu-1996/figures4papers) repository and
the `scientific-figure-making` skill.
