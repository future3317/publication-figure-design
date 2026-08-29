# Typography & Font Specifications

> **Typography contract:** These blocks are backend examples, not copy-verbatim
> requirements. Compile exact family, sizes, and hierarchy from the active journal or
> house profile and verify at final size.

```python
# Publication Figure Design Typography example (backend-specific)
import matplotlib as mpl
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans"],
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 8,
    "figure.titlesize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.frameon": False,
})
```

```r
# Publication Figure Design Typography example (backend-specific)
library(ggplot2)
theme_cns <- theme_bw(base_size = 8, base_family = "Arial") +
  theme(
    axis.title = element_text(size = 8),
    axis.text = element_text(size = 7, color = "#333333"),
    legend.title = element_text(size = 8, face = "bold"),
    legend.text = element_text(size = 7),
    strip.text = element_text(size = 8, face = "bold"),
    panel.grid = element_blank(),
    legend.background = element_blank(),
    legend.key = element_blank()
  )
```

---

## Font Family

Always sans-serif. **Preferred:** Arial, Helvetica. **Fallback:** Liberation Sans.

## Font Size Floor

No text element below 5 pt at final print dimensions. Axis ticks: 5-6 pt. Labels: 6-7 pt. Panel labels: 8-9 pt bold.

## R ggplot2 Setup

```r
library(ggplot2)

theme_cns <- theme_bw(base_size = 8, base_family = "Arial") +
  theme(
    axis.title = element_text(size = 8),
    axis.text = element_text(size = 6),
    legend.title = element_text(size = 7, face = "bold"),
    legend.text = element_text(size = 6),
    strip.text = element_text(size = 8, face = "bold")
  )
```

## R ComplexHeatmap Setup

```r
library(ComplexHeatmap)
library(grid)

ht_opt(
  heatmap_column_names_gp = gpar(fontfamily = "Arial", fontsize = 6),
  heatmap_row_names_gp = gpar(fontfamily = "Arial", fontsize = 6),
  legend_title_gp = gpar(fontfamily = "Arial", fontsize = 7, fontface = "bold"),
  legend_labels_gp = gpar(fontfamily = "Arial", fontsize = 6)
)
```

## Cross-platform Font Notes

- Windows: Arial is installed by default
- macOS: Helvetica is installed by default; Arial is also available
- Linux: Neither Arial nor Helvetica is guaranteed. Use `Liberation Sans` or install `fonts-liberation` / `msttcorefonts`
- For R on Linux: use `showtext` package to register and embed fonts; export with `cairo_pdf()` device
- Always embed fonts in PDF output: `pdf.fonttype: 42` (matplotlib), `cairo_pdf()` (R)

## TeX / TikZ / PGFPlots

For TeX figures, choose the engine from the manuscript font policy: `lualatex` or
`xelatex` with `fontspec` for system/OpenType fonts, or `pdflatex` with an explicit
legacy-font policy. Keep the same family, hierarchy, and final-size minimum as the
active `TypographySpec`; do not let a TeX default silently change sizes. Verify the
compiled PDF for embedded fonts, missing glyphs, and overfull boxes. Read
`references/tex-rendering.md` for the complete source and compile contract.
