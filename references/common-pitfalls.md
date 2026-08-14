# Common Pitfalls Across All Figure Types

These are mistakes that signal "not designed" to reviewers, regardless of the specific chart type.

## Default Color Palettes

```
❌ matplotlib tab10 / tab20 default colors
❌ ggplot2 default hue palette
❌ Excel default color set
❌ jet / rainbow colormap for continuous data

✅ Custom hex color palette (see color-palettes.md)
✅ Semantic colors: green = treatment, purple = control, grey = background
✅ Perceptually uniform sequential colormaps (viridis, cividis, scico)
```

**Why reviewers flag this:** Default palettes are immediately recognizable. They communicate that the author didn't iterate on the figure's design. Jet/rainbow colormaps have non-monotonic luminance, distorting perceived data patterns.

## Over-Decorated Axes

```
❌ Full four-sided border with grey background grid (ggplot2/seaborn default)
❌ Thick axis spines competing with data for visual attention
❌ Heavy gridlines at major AND minor ticks

✅ Left + bottom spines only, thin (0.5-0.6 pt)
✅ No background grid, or very light guide lines (alpha ≤ 0.3)
✅ Ticks facing outward, not inward (inward ticks can overlap data at plot edges)
```

## Legend Problems

```
❌ Legend floating inside the plot area, occluding data points
❌ Legend with default border and background fill
❌ Redundant legend entries (all groups look identical)

✅ Legend outside plot area (bbox_to_anchor) or direct labeling
✅ Legend with no border, transparent background
✅ Merge redundant legend items; use direct annotation for key features
```

## Cross-Panel Semantic Drift

```text
鉂?Global legend lists methods that do not appear in every panel
鉂?The same method changes marker/linestyle between panels
鉂?A panel introduces a new color (for example, an unlabeled purple series)
鉂?A local legend is placed over the data instead of reserving a legend slot
鉂?Long method names and repeated formula y-labels consume the gutter and hide hierarchy
鉂?Wide uncertainty ribbons overlap until lines and markers become the visual background

鉁?Declare one method -> color/linestyle/marker map and reuse it everywhere
鉁?Declare per-panel series membership; use panel-local/direct labels for different baselines
鉁?Keep `unresolved_orphan_series` empty; every visible encoding has a role and label
鉁?Reserve legend space outside the axes and inspect its separation from data
鉁?Use shared/abbreviated axis labels with definitions in the caption or a compact note
鉁?Declare CI/SD/quantile meaning and keep interval alpha low enough to preserve marks
```

This failure pattern is easy to mistake for a palette problem. It is a semantic and layout
problem first: a clean-looking global legend cannot repair a panel that changes the identity
of a method, and a technically valid ribbon can still erase the evidence it is meant to show.

## Font & Typography Issues

```
❌ Default matplotlib font (DejaVu Sans) — looks unpolished in print
❌ Variable font sizes across panels in multi-panel figures
❌ Text rendered at display size then scaled down → illegible at print size
❌ Mixed serif and sans-serif fonts in the same figure

✅ Explicitly set Arial/Helvetica/Liberation Sans
✅ Consistent font sizes within and across panels
✅ Design at print dimensions from the start
```

## Export Mistakes

```
❌ Screenshot or low-resolution PNG as the only deliverable
❌ Rasterized text (text rendered as pixels in a PNG, then placed in a PDF)
❌ PDF with fonts outlined as paths (uneditable)

✅ Vector format (PDF/SVG/EPS) for line art and text
✅ PNG preview at 300 dpi as companion, not as master
✅ Embed fonts properly (see export-specs.md)
```

## Multi-Panel Mistakes

```
❌ Inconsistent panel sizes within the same figure
❌ Missing or inconsistent panel labels (a, b, c...)
❌ Different color scales used for the same variable across panels
❌ Panel spacing so tight that borders merge

✅ Consistent panel dimensions via gridspec/subplot layout
✅ Panel labels in consistent position (top-left of each panel), bold, 8-9 pt
✅ Shared color scale via explicit vmin/vmax or colorRamp2
✅ Adequate spacing (wspace=0.3, hspace=0.3 minimum)
```

## Colorblind Accessibility

```
❌ Red-green as the only distinguishing color pair
❌ No alternative visual channel (only color differentiates categories)

✅ Use blue-orange, blue-purple, or other colorblind-safe pairs
✅ Add shape or linetype as secondary differentiator for critical comparisons
✅ Test with a colorblind simulator
```

## Axis Range Traps

```
❌ Fixed 0-100 axis when all values sit in 85-95
❌ Symmetric y-limits that waste half the panel
❌ Auto-scaled axes that hide meaningful differences

✅ Tighten y-limits to the relevant data range plus a small margin
✅ Use 80-100 when all values are in that band
✅ Make differences visible; do not let the axis swallow the signal
```

See `references/publication-style-patterns.md` for the dynamic y-axis scaling
pattern.

## Print-Safe Bar Encoding

```
❌ Bars that differ only by fill color (blur in grayscale)
❌ No edges on grouped bars
❌ Subgroups relying on hue alone

✅ Black edges on bars: edgecolor="black", linewidth=1.5-3
✅ Hatch patterns for subgroups: "/", "\\", "."
✅ Redundant encoding so the figure remains readable in black-and-white print
```

See `references/publication-style-patterns.md` for bar edge and hatch patterns.

## Statistical Display Traps

```
❌ Bar charts hiding individual data points (show points over bars)
❌ Error bars without explanation (SD? SEM? CI?)
❌ Asterisks without threshold definition in deliverable notes
❌ Log scales not explicitly noted on axis or in caption

✅ Overlay individual data points on bar charts (strip plot + bar)
✅ Clarify error bar type in deliverable notes
✅ Prefer exact p-values; define asterisk thresholds if used
✅ Label log-scaled axes as "log10(Expression)" not just "Expression"
```
