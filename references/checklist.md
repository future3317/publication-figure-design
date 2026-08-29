# QA Protocol

This is an **LLM-executable** quality assurance protocol. It compiles the active
`rules/` sets and the target journal profile into checks; it is not a universal recipe
for one font, one width, one spine model, or one export helper. A house default is a
diagnostic/advisory unless the active profile promotes it to a requirement.

## Automated Validation

Run automated checks on any generated script:
```bash
python publication-figure-design/scripts/qa_validator.py <script.py>
```
This validates AP-0 through CL-8 without human review. See `publication-figure-design/scripts/qa_validator.py` for the full check suite.

## Protocol Structure

The protocol runs in four passes. Pass 0 catches common anti-patterns. Pass 1 verifies code-level compliance. Pass 2 checks visual logic and data integrity. Pass 3 verifies the rendered output. Each failed check includes the fix action.

**Stop condition:** If Pass 0 or Pass 1 finds >2 failures, fix them and re-run the pass before proceeding. A pass with ≤2 minor issues can proceed with warnings noted in the report.

---

## Pass 0: Anti-Pattern Scan (Fast, High-Impact)

Run these checks first. They catch the issues reviewers flag most often and take seconds to verify.

### AP-0: Active Style Contract

**How to check:** Verify that the selected backend consumes the compiled
`TypographySpec`, `PaletteSpec`, `LayoutSpec`, `ComponentSpec`, and export contract.
The following are the generic house defaults, not copy-verbatim requirements:

1. Typography defaults may include explicit family, hierarchy, spine, tick, and legend choices; exact values come from the active journal/house profile and final-size review.
2. Color baseline must declare semantic roles (for example `COLOR_ROLES` or `PALETTE_ROLES`) for background, neutral/context, comparison groups, and focal accent. Exact hex values are selected from scientific meaning and the active reference; one fixed palette must not be injected into every figure.
3. Export is checked by the capability IDs in `references/export-specs.md`; helper names are not required.

**Pass condition:** Active profile requirements are satisfied, semantic color roles are explicit, and any house-default deviation is recorded. Exact colors need not equal a global palette.

**Fix if FAIL:** Compile the active specs and add a figure-specific semantic color-role map. Choose colors only after the scientific roles and active reference are known.

### AP-1: Default Color Palette

**How to check:** Scan the generated code for these patterns. Any match = FAIL.

| Pattern | What it means |
|---------|---------------|
| `cmap='tab10'`, `cmap='tab20'`, `cmap='jet'`, `cmap='rainbow'`, `cmap='hsv'` | matplotlib default colormap |
| `plt.cm.tab10`, `plt.cm.tab20`, `plt.cm.jet` | matplotlib built-in colormap reference |
| `sns.color_palette('deep')`, `sns.set_palette('muted')`, `sns.color_palette()` | seaborn default palette (deep/muted/pastel/bright/dark/colorblind) |
| `palette='deep'`, `palette='muted'`, `palette='Set1'`, `palette='Set2'` | seaborn/ggplot2 default palette name |
| `scale_color_hue()`, `scale_fill_hue()` | ggplot2 default hue scale |
| `scale_color_brewer(palette='Set1')`, `scale_fill_brewer(palette='Set2')` | ggplot2 Brewer qualitative scale |
| `brewer.pal(n, 'Set1')`, `brewer.pal(n, 'Paired')` | RColorBrewer qualitative palette |

**Fix if FAIL:** Replace with custom hex colors. Load `references/color-palettes.md` and choose a semantic palette. Never just swap to viridis —choose colors that serve the figure's scientific message.

**Pass condition:** None of the above patterns appear in the code. Custom hex colors (`#XXXXXX`) are used instead.

### AP-2: Jet / Rainbow Colormap

**How to check:** Search for `jet`, `rainbow`, `hsv` used as colormap names.

**Fix if FAIL:** Replace with a perceptually uniform sequential colormap. For diverging data, use the Publication Figure Design standard `#2166AC - #F7F7F7 - #B2182B`. For sequential, use viridis, cividis, or a custom blue sequential.

**Pass condition:** No jet/rainbow/hsv colormap in continuous data contexts.

### AP-3: Border and Grid Model

**How to check:** Inspect the compiled `LayoutSpec` and final render. A clean
left/bottom spine model is the PFD house default, but a different model is valid when
the family, reference, accessibility need, or journal profile documents it.

- **Python:** `axes.spines.top: False` AND `axes.spines.right: False` (in rcParams or per-axis)
- **R ggplot2:** `theme(panel.grid = element_blank())` or `theme_bw()` + spine removal, or a clean theme
- **R base:** Explicit `bty='l'` or spine removal

**Fix if FAIL:** Repair the active layout contract or record the documented deviation;
do not force a spine recipe merely to satisfy this advisory.

**Pass condition:** The border/grid model is intentional, readable at final size, and
does not compete with evidence.

### AP-4: Legend Occlusion

**How to check:** Look for `ax.legend()` or `plt.legend()` called without `bbox_to_anchor` OR `loc` outside the plot area, where the legend would default to inside the plot. Also check R: `theme(legend.position = c(...))` with coordinates inside the plot area.

**Fix if FAIL:** Move legend outside: `ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False)` in Python; `theme(legend.position = 'right')` or `'bottom'` in R. Alternatively, use direct labeling (annotate data points/lines directly).

**Pass condition:** Legend outside plot area, or justified internal placement with no data occlusion, or direct labeling used instead.

**Multi-panel semantic check:** A global legend is valid only when every listed method/condition
appears with the same color, linestyle, and marker wherever it is plotted. If panels use different
baselines or subsets, declare `panel_series` and use panel-local/direct labels; a panel-only color,
marker, or renamed series is an unresolved orphan and receives FIX. Inspect the legend against the
actual data region, not just its bounding box.

**Uncertainty check:** Every ribbon declares CI/SD/quantile meaning and alpha. Overlapping ribbons
must remain subordinate to lines and markers; if they wash out the data, reduce alpha, separate
draw order, or use error bars/small multiples.

### AP-5: Low-Resolution Export Only

**How to check:** Does the code include a vector export (`savefig(..., '*.pdf')`, `savefig(..., '*.svg')`, `ggsave('*.pdf')`, `ggsave('*.svg')`, `cairo_pdf()`, `pdf()`)? If only PNG/JPG export is present, FAIL.

**Fix if FAIL:** Add vector export. Python: `fig.savefig('figure.pdf', bbox_inches='tight', dpi=300)`. R: `ggsave('figure.pdf', device=cairo_pdf)`.

**Pass condition:** At least one vector format export (PDF/SVG/EPS) present in the code.

### AP-6: Missing Individual Data Points (Small n)

**How to check:** If the figure is a bar chart or boxplot, and the sample size appears small (n < 10 per group from the data or from context), verify individual data points are shown. Check for `stripplot`, `swarmplot`, `geom_point`, `geom_jitter`, or `scatter` overlay.

**Fix if FAIL:** Overlay individual points. Python: `sns.stripplot()` or `ax.scatter()` with jitter. R: `geom_point(position = position_jitter(width = 0.1))`.

**Pass condition:** Individual data points visible for bar/box plots with small n. If n is clearly large (>30 per group), this check is N/A.

### AP-7: Default Font

**How to check:** Verify the font family is explicitly set to Arial, Helvetica, or Liberation Sans. Check for `font.family` or `font.sans-serif` in Python rcParams; `base_family` or `element_text(family=...)` in R.

**Fix if FAIL:** Python: add `font.sans-serif: ['Arial', 'Helvetica', 'Liberation Sans']` to rcParams. R: add `base_family = 'Arial'` to theme or use `showtext` package.

**Pass condition:** Font family explicitly set to Arial/Helvetica/Liberation Sans, not left at system default (DejaVu Sans, R default sans).

---

## Pass 1: Code-Level Compliance

Each check includes: **what to scan for**, **the pass condition**, and **the fix if failed**.

### CL-1: Font Size Floor

**Scan for:** All fontsize declarations in the code.
- Python: `font.size`, `fontsize=`, `labelsize`, `titlesize` parameters
- R: `base_size`, `element_text(size=)`, `gpar(fontsize=)`

**Pass condition:** No fontsize value < 5. The base/default fontsize is 7 (typically 6-7 for journal figures).

**Fix if FAIL:** Bump the sub-5pt value to 5. For axis tick labels on dense figures, 5pt is acceptable. For anything else, use 6-7pt minimum.

### CL-2: Figure Dimensions

**Scan for:** Figure size declarations.
- Python: `figsize=(W, H)`, `W * mm_to_inch`, `W / 25.4`
- R: `width = W, height = H` with `units = 'mm'` or `'in'`

**Pass condition:** Width is within ±3mm of 89mm (single-column) or 183mm (double-column). Height ≤247mm.

**Fix if FAIL:** Adjust dimensions to match the target column width. Recalculate: `figsize=(89/25.4, height/25.4)` for single-column.

### CL-3: Export DPI

**Scan for:** `dpi=` in savefig/ggsave, `res=` in R png/tiff devices.

**Pass condition:** DPI ≥300 for raster exports. Vector exports (PDF/SVG) don't need DPI but having dpi=300 is harmless.

**Fix if FAIL:** Set `dpi=300` in all save calls. Default matplotlib DPI is 100 —insufficient for print.

### CL-4: Font Embedding

**Scan for:** `pdf.fonttype`, `svg.fonttype` in Python rcParams. `cairo_pdf` or `showtext` usage in R.

**Pass condition:** `pdf.fonttype: 42` present (Python). `cairo_pdf()` or `showtext` used (R). `svg.fonttype: 'none'` present (Python, if SVG export used).

**Fix if FAIL:** Add `"pdf.fonttype": 42` and `"svg.fonttype": "none"` to rcParams (Python). Use `cairo_pdf()` device (R).

### CL-5: Spine Linewidth

**Scan for:** `axes.linewidth` in Python rcParams. `axis.line` or `panel.border` theme elements in R.

**Pass condition:** Spine linewidth is 0.5-0.6pt. Data elements (lines, points) use thicker strokes.
(Authoritative source: `references/journal-specs.md` Spines and Axes)

**Fix if FAIL:** Set `axes.linewidth: 0.6` in rcParams (Python) or adjust `axis.line` in theme (R). The default 1.0-1.5pt spine is too heavy for journal figures.

### CL-6: Tick Direction

**Scan for:** `xtick.direction`, `ytick.direction` in Python rcParams. `axis.ticks` theme in R.

**Pass condition:** Ticks directed outward (`'out'`), not inward. Inward ticks can overlap data at plot boundaries.

**Fix if FAIL:** Set `xtick.direction: 'out'` and `ytick.direction: 'out'` in rcParams.

### CL-7: Export Completeness

**Scan for:** Save/export calls in the code.

**Pass condition:** At least one vector save (`*.pdf`, `*.svg`, or `*.eps`) AND at least one raster preview (`*.png` or `*.tiff` at 300 dpi). Both must exist in the delivered code.

**Fix if FAIL:** Add the missing export. Always deliver both formats.

---

## TeX backend checks (when `backend=tex`)

Run `scripts/check_tex_source.py` before compilation. Treat shell-escape tokens,
unbalanced document environments, missing required package declarations, and missing
physical-size bindings as actionable findings. Compile with `-halt-on-error`, then
inspect the log for overfull boxes, undefined references, package errors, and missing
glyphs. Audit PDF page geometry and embedded fonts, render a final-size PNG, and run
the same overlap, clipping, contrast, hierarchy, and uncertainty checks as other
backends. A compiling `.tex` file is not sufficient for READY.

## Pass 2: Visual Logic & Data Integrity

These checks require reasoning about what the code produces, not just pattern matching. The LLM reads the code, imagines the output, and verifies visual logic.

### VI-1: Core Conclusion Visibility

**Question:** If a reviewer looks at this figure for 3 seconds, do they see the core conclusion from Step 0?

**How to check:** Look at the code's visual hierarchy —which element has the strongest visual weight (largest, most saturated color, most prominent position)? Does that element carry the conclusion? Or is a secondary element visually dominant?

**Pass condition:** The element carrying the core conclusion is visually dominant. If the hero element and the conclusion don't align, FAIL.

**Fix if FAIL:** Adjust visual weights —increase hero element size/saturation, reduce competing elements, reposition. If the conclusion can't be made visually dominant, the figure needs restructuring.

### VI-2: Color Accessibility

**Question:** Is the figure interpretable in greyscale? Are red and green the only distinguishing colors for any critical comparison?

**How to check:**
1. Scan for `#FF0000`/`red` AND `#00FF00`/`green` used as the only two category colors
2. Verify at least one non-color differentiator exists for critical comparisons (shape, line style, direct label, faceting)

**Pass condition:** No red-green only pair for critical comparisons. At least one of: additional differentiator, colorblind-safe palette, or direct labels.

**Fix if FAIL:** Add shape/linetype differentiation, or swap the red-green pair for blue-orange or blue-purple. For continuous data, ensure the colormap is perceptually uniform.

### VI-3: Data-Ink Ratio

**Question:** Is any visual element present that doesn't carry information?

**How to check:** Look for: gridlines (especially major AND minor), decorative borders, redundant legend entries, unnecessary background fills, chartjunk (3D effects on 2D data, gratuitous gradients, drop shadows).

**Pass condition:** All visual elements serve a data-communication purpose. Gridlines absent or minimal (very light, major only). No decorative elements.

**Fix if FAIL:** Remove the non-data element. If gridlines are needed for reader guidance, use `color='#E0E0E0', linewidth=0.3, alpha=0.3`.

### VI-4: Axis Range Correctness

**Question:** Does the y-axis range serve the data, or does it mislead?

**How to check:**
1. Does the y-axis start at 0 for bar charts? (Required —bars encode value by length from baseline)
2. For non-bar charts, is the axis range close to the data range? (If all values are 80-95, the axis should be ~75-100, not 0-100)
3. For log scales, is the scale explicitly noted in the axis label?

**Pass condition:** Bar charts start at 0. Non-bar axes are tight to data. Log scales labeled.

**Fix if FAIL:** Adjust axis limits. For bars: `ax.set_ylim(0, ...)`. For non-bars: `ax.set_ylim(data_min*0.9, data_max*1.1)`.

### VI-5: Statistical Annotation Completeness

**Question:** Are statistical claims supported by visible evidence?

**How to check:** If the code includes significance brackets, p-values, or statistical annotations, verify:
1. The test used is named or inferable from context
2. Error bars are defined (SD, SEM, CI —which one?)
3. n is stated or computable from the data
4. Asterisk thresholds are defined if asterisks used

**Pass condition:** Statistical annotations are complete and self-contained. A reader doesn't need the caption to understand what the stats mean.

**Fix if FAIL:** Add the missing information. Prefer exact p-values over asterisks. Define error bar type in a code comment or on the figure.

### VI-8: Relationship and Encoding Grammar

**Question:** Does the visual grammar match the data relationship, and does each variable have one clear primary visual channel?

**Pass condition:** The contract classifies the figure as paired, continuous, independent, or operating-point; every connector represents a real pairing or observed sequence; uncertainty is identified (SD/SEM/CI/etc.) and visually subordinate to estimates; and method/condition/uncertainty are not redundantly or ambiguously encoded. When numeric x positions are merely method-specific locations, a categorical/aligned layout or explicit operating-point composition is preferred over a wide continuous-axis template.

**Fix if FAIL:** Redesign the layout or encoding before adjusting palette, font, alpha, or line width. Separate connector, estimate, and uncertainty layers; merge the legend or direct-label the few conditions; and inspect the result at final physical size and thumbnail scale.

### VI-9: Dense-curve and uncertainty grammar

For frontier, evaluation, or time-series panels, verify that raw observations,
declared trends, uncertainty, reference lines, and claim-bearing points have
separate visual jobs. High-frequency jaggedness must not be silently smoothed away;
overlapping ribbons must not form unreadable mixed blocks; and reference-line labels
must be placed in clear space. If valid domains differ between series, state the
common range or the domain difference rather than implying an accidental truncation.

**Pass condition:** The plot's layer order and transforms are recoverable from the
source/render trace, and the final-size image preserves series identity and trend
readability.

### VI-10: Composite, inset, and range stress

For multi-panel, inset, geometry, or bar/interval figures, check panel area against
evidence importance, remove repeated skeleton/reference elements with no new reading
job, and verify that inset connectors do not cross the inset or collide with axes.
Dense ellipsoid/node/3D overlays require fill/edge/wireframe/marker hierarchy.
Extreme ranges require a declared log/broken-axis/inset treatment or an explicit
outlier annotation; never crop or rescale silently.

**Pass condition:** Every panel and inset has a clear source-to-evidence reading path,
and no extreme mark, overlay, or empty margin suppresses the intended comparison.

### VI-6: Panel Label Consistency (Multi-Panel Only)

**Question:** Are panel labels consistent in position, font, and style?

**How to check:** Verify all panel label calls use the same coordinate system, same fontsize, same fontweight, and same position offset. Check for mixed placement strategies (top-left on panel a, bottom-right on panel d).

**Pass condition:** All labels use identical styling and positioning. No label is missing.

**Fix if FAIL:** Unify all label calls to the same pattern. Standard: `ax.text(-0.12, 1.02, label, transform=ax.transAxes, fontsize=8.5, fontweight='bold')`.

### VI-7: Revision Case Cross-Reference

**Question:** Does this figure type + journal combination match any known peer-review rejection patterns?

**How to check:** Load `references/revision-cases.md`. Scan the cases for matches against:
1. The user's figure type (e.g., heatmap, volcano, bar chart)
2. The user's target journal (if specified)
3. Common failure patterns for that figure type (e.g., "heatmap → default red-blue colormap", "volcano → missing threshold lines", "bar chart → no individual data points when n < 10")

**Pass condition:** For each matching case, the generated code must NOT contain the failure pattern described. If a case warns about default colormaps and the code uses `cmap='jet'`, FAIL.

**Fix if FAIL:** Apply the fix described in the matching revision case. Each case includes the exact reviewer comment, the fix action, and the lesson learned.

**Example matches:**
- Heatmap + Nature Genetics → check Case 1 (default red-blue colormap)
- Bar/box + n < 10 → check Case 2 (missing individual data points)
- Volcano → check Case 3 (missing significance thresholds)
- Multi-panel → check Case 4 (inconsistent styling across panels)
- Schematic/model → check Case 10 (inconsistent visual language)
- Correlation heatmap → check Case 8 (missing mask fill)
- Phylogenetic tree → check Case 9 (illegible tip labels)

---

## Pass 3: Visual Verification (Render + Inspect)

Passes 0-2 verify the **code**. Pass 3 verifies the **output**. These are problems invisible in code but obvious in the rendered figure.

### VV-1: Data Occlusion

**Question:** Does any visual element cover or overlap data points, labels, or other critical information?

**How to check:** Inspect the rendered PNG. Look for:

| Issue | Where to Look |
|-------|--------------|
| Legend overlapping data | Legend bounding box vs scatter/bar coordinates |
| Gene/point labels overlapping each other | Dense regions near label annotations |
| Colorbar crowding plot area | Right edge of heatmap/UMAP |
| Error bars crossing axis labels | Bottom/top margins |
| Panel labels covering data | Top-left corner of each panel |

**Fix if FAIL:**
- Legend occlusion —`bbox_to_anchor=(1.02, 1)` to move outside, or adjust `loc` to an empty corner
- Label overlap —reduce fontsize by 1pt, increase xytext offset, or label fewer items; use `adjustText` (Python) or `ggrepel` (R) for automatic label avoidance
- Colorbar crowding —increase `pad` parameter, reduce `shrink`, or move colorbar to horizontal below the plot
- Error bar collision —increase y-axis upper limit by 10-15%
- Panel label occlusion —move label offset from (-0.08, 1.02) to (-0.15, 1.04)

**Pass condition:** No data occlusion visible. All labels, legends, and annotations are clearly separated from data elements.

### VV-1a: Text, curve, and callout clearance

At final display size, inspect title/panel-label/legend/axis/annotation bounding
boxes and their intersections with data marks. Also inspect curve/annotation,
reference-line label, inset-connector, and bar-top-label collisions. A light text
color on a light fill is a failure even when it appears acceptable in an enlarged
preview. Repair by moving, restructuring, or adding a local backing/edge; do not
solve a semantic collision by merely shrinking all text.

### VV-1b: Series and uncertainty separation

When curves, bands, nodes, ellipsoids, or image detail overlap, verify at final size
that each critical series remains traceable in grayscale and under reduced scale.
Use redundant channels and layer hierarchy where color alone or weak dashed lines
merge. A muddy translucent overlap, indistinguishable marker set, or unreadable
representative object is a FIX, not a cosmetic warning.

### VV-2: Layout Regularity

**Question:** Do panels align properly? Are margins consistent? Is the figure balanced?

**How to check:** Inspect the rendered PNG. Look for:
- Uneven panel widths/heights in a grid
- Misaligned panel edges
- One panel much smaller/larger than peers (unless intentional hero panel)
- Text cut off at figure boundaries
- Excessive or inconsistent whitespace between panels
- Colorbar extending beyond panel boundary

**Fix if FAIL:**
- Uneven panels —enforce explicit `width_ratios` and `height_ratios` in gridspec; use `sharex=True, sharey=True` for same-axis panels
- Text cut off —increase figure margins: `gs.update(left=0.12, bottom=0.12)` or use `bbox_inches='tight'`
- Uneven spacing —use consistent `wspace` and `hspace` values across the entire gridspec
- One panel dominating —check if it's the intended hero panel; if not, adjust `height_ratios` or `width_ratios`

**Pass condition:** Panels are aligned, margins are consistent, no text is cut off, and the layout looks intentional.

### VV-3: Text Legibility

**Question:** Is all text actually readable at the rendered size?

**How to check:** Inspect the rendered PNG. This is the ground truth —code-level fontsize checks in CL-1 verify the setting, but only visual inspection verifies the result. Check:
- Axis tick labels —especially long strings or rotated labels
- Gene/protein names —italic text at small sizes can blur
- Legend text —often the smallest text on the figure
- Colorbar tick labels —can be crushed if the colorbar is narrow
- Panel labels —should be immediately visible, not lost in margin clutter

**Fix if FAIL:**
- Tick labels too small —bump from 5pt to 6pt, or rotate 45° instead of 90°
- Gene labels illegible —increase from 4pt to 5pt, or switch from italic to regular (regular text is more legible at small sizes than italic)
- Legend unreadable —increase fontsize by 1pt, reduce legend content, or move to larger panel
- Colorbar labels crushed —increase colorbar width (`aspect=10` instead of `aspect=15`)

**Pass condition:** The reader can read every text element without squinting, at the intended print size.

### VV-4: Color Rendering

**Question:** Do colors render as intended? Are adjacent colors distinguishable?

**How to check:** Inspect the rendered PNG. Verify:
- Adjacent categorical colors are visually distinct (not two shades of the same hue)
- Gradient/sequential colormaps show visible progression (not all looking like the same color)
- Threshold lines are visible against the background data density
- Grey NS points in volcano/UMAP don't overpower colored signal points
- White or very light elements are visible against white background

**Fix if FAIL:**
- Adjacent colors too similar —increase hue separation; swap one for a color further away on the color wheel
- Gradient invisible —increase `vmin`/`vmax` range, or switch to a higher-contrast colormap
- Threshold line lost —darken line color to `#444444`, increase linewidth to 0.8pt, or add a subtle annotation
- NS points overpower signal —reduce NS point alpha from 0.4 to 0.25, or plot NS points first (lower zorder)
- Light elements invisible —add a very thin dark edge (`edgecolors='#CCCCCC', linewidth=0.1`)

**Pass condition:** All color distinctions are clearly visible. Nothing blends into the background or another category.

### VV-4a: Text-on-Fill Contrast

**Question:** Is every in-cell annotation readable against its actual local fill, rather than merely visible in enlarged preview?

**How to check:** For heatmaps, matrices, colored tiles, nodes, or callout boxes carrying text, annotations call `pick_text_color(cell_color)` and every declared text region passes `scripts/rendered_contrast.py` at `contrast_ratio >= 4.5:1`.

**Fix if FAIL:** Use `pick_text_color(cell_color)` for each tile; do not globally set annotations to white. If the strongest black/white choice still fails, alter the fill lightness or remove/inset the text.

**Pass condition:** No light-on-light or dark-on-dark text remains in the final raster.

### VV-5: Data Validity & Render Integrity

This gate verifies that the rendered marks faithfully represent the bound source data;
it does **not** require a relationship, effect size, variance, or classification signal
to be scientifically strong. A null result is a valid result.

Apply these rule IDs from `rules/global/scientific-integrity.yaml` and
`rules/global/provenance-reproducibility.yaml`:

| Rule | Check | Failure action |
|---|---|---|
| DATA-001 | arrays are non-empty and finite where the domain requires | block render and repair the binding/data contract |
| DATA-002 | graphical marks reproduce source values after declared transforms | block and reconcile `RenderTrace` |
| DATA-003 | axis limits do not silently exclude valid observations | block and record an explicit domain decision |
| DATA-004 | clipping, saturation, and masked values are reported | block or warn according to the target policy |
| DATA-005 | computed statistics reproduce from bound data | block and recompute from the source |
| DATA-006 | synthetic/demo data are explicitly labeled | block production evidence; allow clearly labeled draft |
| DATA-007 | synthetic parameters were not tuned to manufacture a conclusion | block and restore the scientific contract |
| DATA-008 | blank or unusually dense panels trigger inspection | warn/manual review; never tune data to pass |

Content density is a rendering diagnostic only. It cannot be used as a proxy for
scientific signal, and fixes must never change effect size, noise, sample count, or
filtering merely to make a plot look more persuasive.

### Visual Verification Protocol

1. **Render the figure** —Run the generated code. If Python/R is not available locally, skip Pass 3 and flag the limitation to the user.
2. **Inspect methodically** —Check VV-1 through VV-5 in order. Do not scan —focus on each check individually.
3. **Fix and re-render** —Each FAIL requires a code fix AND re-rendering. Fix all VV issues, re-render, and re-inspect. Maximum 3 render-fix cycles.
4. **Escalate if stuck** —If 3 cycles don't resolve the issues, the layout likely needs restructuring. Escalate to Reviewer Simulation Mode for a wider diagnosis.

**Pass 3 report format:**
```
Pass 3 —Visual Verification:
  [PASS] VV-1: No data occlusion
  [FAIL] VV-2: Panel (c) legend extends beyond figure right edge —adjust bbox_to_anchor
  [PASS] VV-3: All text legible at 300dpi
  [WARN] VV-4: Treatment blue (#2166AC) vs Knockout green (#1B7837) distinct but check greyscale
  [FAIL] VV-5: AUROC AUC=0.94 curve saturates —tpr>0.99 at fpr=0.05, formula blowup
```

---

## Reference Fidelity Pass (Concrete Reference Only)

Run this pass after Pass 3 whenever the request uses a concrete reference image. Load `references/reference-driven-reconstruction.md`, inspect the equal-size comparison, and run `scripts/check_reference_fidelity.py`.

### RF-1: Reference inspected

**Pass condition:** The actual reference image was opened and inspected. Metadata, tags, filenames, or memory alone do not pass.

### RF-2: Reconstruction contract complete

**Pass condition:** Every required Reference Reconstruction Contract field is non-empty, and `must_match` contains observable features.

### RF-3: Implementation decision justified

**Pass condition:** `reuse`, `restructure`, or `rewrite` follows the five-dimension decision contract. `reuse` includes compatibility evidence for panel topology, mark geometry, layer topology, data encoding, and annotation/legend model.

### RF-4: Layout and geometry correspond

**Pass condition:** Canvas ratio, panel topology, relative panel sizes, and primary mark geometry match every applicable `must_match` item.

### RF-5: Layers and encodings correspond

**Pass condition:** Layer order, overlays, marginal/inset relationships, axes, scales, and visual-variable mappings reproduce the reference grammar without changing scientific meaning.

### RF-6: Palette roles correspond

**Pass condition:** Background, neutral, group, and accent colors serve the same semantic roles and similar visual proportions. Copying hex values while changing their roles fails.

### RF-7: Typography and finishing correspond

**Pass condition:** Font hierarchy, legend model, direct labels, annotations, whitespace, density, and focal hierarchy correspond at the final publication width.

### RF-8: No irrelevant old skeleton remains

**Pass condition:** The candidate contains no panels, layers, legend model, annotations, or layout retained solely because they existed in old code. Cosmetic-only adaptation fails.

### RF-9: Equal-size comparison inspected

**Pass condition:** A non-empty side-by-side comparison exists, preserves both aspect ratios, and was inspected at the target display width.

### RF-10: Deviations justified

**Pass condition:** Every `must_match` item is `pass` or `justified_deviation`. Each deviation names a scientific, data, accessibility, or journal reason. Convenience and time pressure are invalid reasons.

**Reference gate:** Any failed RF check or any unresolved `must_match` item sets the verdict to FIX. Revise, rerender, recreate the comparison, and rerun the checker. Do not deliver a claim that the output matches the reference until the checker returns READY.

## Visual Optimization Pass (Existing Figure Optimization Only)

For optimize/polish/beautify/improve/redesign requests, first run `scripts/prepare_visual_optimization.py`; it owns the recommendation call and saves the packet. Then run `scripts/check_visual_optimization.py` with readable before, selected-reference, after, and equal-cell comparison images. READY requires candidate IDs to match the packet, a pixel observation for every returned candidate, a structural selection reason, an explicit palette decision (including justified retention), a stable cross-panel series-encoding contract with no unresolved orphan series, an uncertainty/overlap contract, an observable diagnosis of the old render, at least one structural/encoding/legend-model change, and a completed final-size review for hierarchy, panel balance, whitespace, legend footprint, text legibility, cross-panel semantics, legend/data separation, uncertainty legibility, and axis-label compactness. Run `scripts/rendered_contrast.py` for every annotation on a colored fill; contrast below 4.5:1 receives FIX. Cosmetic-only edits receive FIX even if Passes 0-3 pass.

---

## QA Report Format

After executing all four passes, output a structured report:

```
============================================================
Publication Figure Design QA Report
============================================================
Figure: [brief description]
Target: [journal], [single/double] column
Backend: [Python/R]

Pass 0 —Anti-Pattern Scan:
  [PASS] AP-1 Default Color Palette
  [PASS] AP-2 Jet/Rainbow Colormap
  [FAIL] AP-3 Four-Sided Borders —top/right spines not removed
  [PASS] AP-4 Legend Occlusion
  ...

Pass 1 —Code Compliance:
  [PASS] CL-1 Font Size Floor (min 6pt)
  [FAIL] CL-2 Figure Dimensions —width 120mm, not 89mm or 183mm
  ...

Pass 2 —Visual Logic:
  [PASS] VI-1 Core Conclusion Visibility
  [WARN] VI-2 Color Accessibility —red-green pair used, add shape differentiation
  ...

Pass 3 —Visual Verification (render required):
  [PASS] VV-1: No data occlusion
  [PASS] VV-2: Layout regular, panels aligned
  [FAIL] VV-3: Gene labels at 4pt italic are illegible —increase to 5pt
  ...

Reference Fidelity (when a concrete reference is used):
  [PASS] RF-1 through RF-3: reference inspected, contract complete, decision justified
  [FAIL] RF-4: candidate retains a single-axis layout instead of the reference 2x2 topology
  [PASS] RF-5 through RF-10

Visual Optimization (when an existing figure is optimized):
  [PASS] Before/reference/after images readable and comparison authentic
  [PASS] Selected reference opened; structural changes recorded
  [PASS] Final-size hierarchy, balance, whitespace, legend, and text review complete

Summary:
  Pass: X/Y   Fail: X/Y   Warn: X/Y

Verdict:
  [READY] —All checks passed. Deliver.
  [FIX]  —N failures need attention. Fix and re-run this protocol.
  [WARN] —Deliverable with caveats noted above.

============================================================
```

## After QA

- **READY —** All passes (0-3) clear, plus RF-1 through RF-10 when a concrete reference is used. Proceed to Hub Step 7 (Deliver). Include the full QA report with delivery.
- **FIX —** Fix failed items, re-run only the failed pass, then re-render for Pass 3 if visual changes were made. Maximum 3 render-fix cycles.
- **WARN —** Deliver with warnings noted. Flag to the user.
- **SKIP Pass 3 —** For ordinary create/review work, if Python/R runtime is unavailable, warn that visual verification was skipped. For visual optimization, a missing render/runtime blocks a completion claim because the before/reference/after gate cannot run.

If >2 failures remain after one round of fixes, or Pass 3 issues persist after 3 render-fix cycles, escalate to **Reviewer Simulation Mode** (Hub SKILL.md, Reviewer Simulation section) for a wider diagnosis.

If >2 failures remain after one round of fixes, the figure likely has structural issues. Escalate to **Reviewer Simulation Mode** (Hub SKILL.md, Reviewer Simulation section) for a wider diagnosis before attempting more fixes.
