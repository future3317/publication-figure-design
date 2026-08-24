# Global Visual Language

> This document is the readable companion to the machine-readable rules under
> `rules/`. Scientific invariants live in `rules/global/`; the preferences below
> are PFD house defaults in `rules/house/`. Do not treat a house preference as a
> journal hard requirement or as evidence that a scientific effect should exist.

Rule precedence is: scientific integrity → accessibility/legibility → journal hard
requirements → explicit user requirements → family rules → house defaults → backend
defaults. Conflicts between non-overridable rules block the run and are reported.

This is the default visual baseline for every figure family. Scientific meaning,
uncertainty semantics, explicit user requirements, journal constraints, and an
inspected concrete reference take precedence; any visual deviation is recorded in
the `StyleSpec` rather than left as an informal preference.

## Baseline rules

### Visual-failure priority

During critique and repair, fix failures in this order:

1. overlap, clipping, or unreadable text;
2. invalid or ambiguous data encoding;
3. panel hierarchy, composition, and whitespace imbalance;
4. indistinguishable series or uncertainty layers;
5. palette polish and decorative refinement.

This order is structural: a polished palette never compensates for a collision,
ambiguous curve grammar, or a panel that cannot be read at final size.

- **Soft segmentation:** separate panels and semantic regions with whitespace,
  alignment, subtle tonal shifts, or thin separators. Avoid heavy boxes, dark
  dashboard grids, and borders that compete with the evidence.
- **Short title hierarchy:** use concise panel titles that name the evidence job,
  not sentence-length explanations. Keep title, axis/body, tick, and annotation
  sizes visibly ordered; put detail in labels, captions, or the manuscript text.
- **Whitespace is structural:** preserve outer margins, panel gutters, label
  clearance, and breathing room around annotations. Do not fill empty space merely
  to make a panel look busy or symmetrically packed.
- **Low-saturation semantic colors:** assign a stable role to each color and use
  restrained chroma for fills and secondary series. Keep the focal accent sparse;
  low saturation must never mean low contrast for text, strokes, or critical marks.
- **Restrained legends and annotations:** prefer direct labels when they improve
  lookup; otherwise use one compact legend with only required entries. Annotate
  claim-bearing events, thresholds, uncertainty, or exceptions, and remove
  duplicated legend/callout/panel text.

## Compilation contract

Compile these rules into `LayoutSpec`, `TypographySpec`, `PaletteSpec`, and
`ComponentSpec` during Design Spec/Binding. Renderers consume those tokens explicitly;
they do not reinterpret this baseline through backend defaults. A concrete reference
can change the grammar only after pixel inspection and an explicit recorded reason.

## Scientific figure-design principles

These principles are mandatory for scientific figure work, not optional style advice.

### Figure-versus-table preflight

Before choosing a chart or writing plotting code, ask what information would be lost if
the result were replaced by a table. Use figures for patterns, geometry, distributions,
mechanisms, qualitative differences, spatial structure, or continuous relationships.
Use tables for exact scalars, mean ± SD, benchmarks, ablations, latency, memory,
parameters, and small categorical comparisons. If replacing the figure with 3–5 numbers
loses almost no information, keep it in a table and do not create a redundant chart.

### Scientific meaning and output fidelity

- Choose the figure family from data semantics, never from visual novelty. Prefer
  reliability curves for calibration, ECDF/KDE/violin for distributions, scatter or
  density contours for two continuous variables, interval plots for effects with CI,
  DAGs for reachability, spatial glyphs/ellipsoids for geometric uncertainty, and
  line curves for ordered time or training processes. Treat radar, pie, decorative
  heatmaps, tiny bar charts, spaghetti lines, and seed-only figures as deliberate
  exceptions requiring a stated evidence reason.
- **visualize model outputs, not only metrics**: show input → prediction →
  uncertainty/structure when the output has meaningful geometry or qualitative content.
- Preserve the mathematical domain and actual data. **do not invent or exaggerate
  scientific effects**; do not smooth away observed structure, enlarge uncertainty,
  imply a physical-space covariance for transformed-space uncertainty, or change a
  shared mean/scale merely to make panels look more different.
- Make spatial relationships explicit: attach uncertainty glyphs to the object they
  describe, show input → prediction, and make the core object large enough to read at
  final size. Crop to an informative region rather than shrinking the subject to a
  postage stamp.

### Controlled comparison and semantic consistency

- For qualitative method comparisons, hold **the same sample, camera, crop, scale**,
  axes, and controlled prediction mean fixed; vary only the experimental quantity.
  **one visual variable per experimental variable** is the comparison contract.
- Structural or output differences are evidence; color is only a supporting channel.
  Keep semantic colors stable across the paper (for example baseline/reference,
  model families, and controls) and never let a color silently change meaning between
  figures.
- A **main figure answers one scientific question**. Prefer 1–3 meaningful panels,
  usually one dominant qualitative/hero panel plus compact supporting evidence. Avoid
  dashboard grids that repeat titles, axes, legends, error bars, and numbers.
- Preserve continuity when sample-level data carry shape information: use ECDF, KDE,
  hexbin, density contours, reliability curves, or conditional trends instead of
  automatically collapsing everything to mean ± SD. Label a descriptive trend as
  descriptive; do not imply an inferential CI without an appropriate independence
  and uncertainty definition. Seed variability usually belongs in a table unless it
  is itself the scientific question.

### Text, caption, table, and paper rhythm

- Keep figure text to short titles, axes, method labels, and crucial values; the
  **caption carries the explanation** of what was plotted, the protocol, how to read
  it, the finding, and what cannot be inferred.
- Tables are scientific reading aids: use booktabs-like hierarchy, no vertical rules,
  restrained highlighting, and separate blocks for different experimental protocols.
  Merge panels only when their intervention and semantics are genuinely the same.
- Build a paper-level visual rhythm (overview → mathematical/geometry meaning → internal
  mechanism → application qualitative evidence → distribution or continuous evidence)
  rather than a sequence of unrelated chart types.

## Mandatory preflight

The figure-versus-table preflight, semantic family choice, mathematical-domain check,
controlled-comparison check, object/uncertainty attachment check, and cross-figure color
role check **must run before rendering**. Record their decisions in the TaskSpec or
DesignPacket. A failed preflight blocks Render until the scientific contract or design
spec is repaired.
