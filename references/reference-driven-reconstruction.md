# Reference-Driven Reconstruction

Use this protocol when the user supplies, points to, selects, or explicitly asks to match a concrete reference image. It applies to both creating and revising figures.

It also applies to every visual-optimization request. When no reference was supplied, select one from reviewed/promoted library entries using `visual-reference-library.md`; open the actual pixels before editing.

## Iron rule

Scientific meaning and data integrity come first. After those, the selected reference's structure and visual language outrank production assets and skill defaults.

Existing plotting code is implementation material, not a design constraint. If its visual grammar is incompatible, restructure or rewrite it.

## Required sequence

1. Open every selected reference image. Do not rely on tags, filenames, metadata, or memory.
2. Write the Reference Reconstruction Contract before selecting a production asset or editing plotting code.
3. Classify the implementation as `reuse`, `restructure`, or `rewrite`, and record the corresponding unified `adaptation_level`.
4. Implement and render at target publication dimensions.
5. Produce a side-by-side comparison at equal displayed size.
6. Inspect every `must_match` feature and record `pass` or `justified_deviation`.
7. Run `scripts/check_reference_fidelity.py`.
8. If the result is FIX, revise and rerender. Deliver only after READY.

## Precedence

1. Scientific meaning, complete data, non-misleading encoding
2. Explicit user requirements
3. Concrete reference structure and visual language
4. Reusable production code
5. Skill defaults

A reference may control canvas ratio, panel topology, mark geometry, layers, annotations, legend, spacing, typography, palette roles, and visual hierarchy. It may not change the scientific question, fabricate observations, hide inconvenient data, or force an invalid statistical encoding.

For paired comparisons, operating points, and uncertainty-bearing marks, the reference cannot override the data relationship. Classify the production figure as paired, continuous, independent, or operating-point before borrowing a visual grammar. Do not copy a continuous-axis errorbar layout when the data are only a few method-specific states; preserve the truthful relationship and adapt the composition (for example, categorical alignment, dumbbells, or small multiples).

## Reference Reconstruction Contract

Create a JSON contract with these fields:

```json
{
  "reference_source": "path or reference id",
  "scientific_invariants": ["meaning and data properties that cannot change"],
  "canvas_layout": "aspect ratio, panel topology, relative panel sizes",
  "mark_geometry": "marks, shapes, distributions, bands, lines",
  "layer_topology": "draw order, overlays, marginal/inset relationships",
  "data_encoding": "variables mapped to position, color, size, shape, facets",
  "palette_roles": "background, primary groups, neutral context, accent and proportions",
  "typography": "font hierarchy, weight, size relationships",
  "legend_annotation": "legend model, direct labels, callouts, statistics",
  "spacing_hierarchy": "whitespace, density, focal element",
  "must_match": ["observable features required for faithful reconstruction"],
  "may_adapt": [{"feature": "item", "reason": "scientific/data reason"}],
  "implementation_decision": "reuse | restructure | rewrite",
  "adaptation_level": "exact_reuse | structural_adaptation | style_only | build_new",
  "decision_evidence": "comparison between candidate code and reference grammar",
  "structural_compatibility": ["five required dimensions when decision is reuse"],
  "structural_changes": ["non-cosmetic implementation changes"],
  "fidelity_review": [
    {"feature": "must-match item", "status": "pass | justified_deviation", "reason": ""}
  ]
}
```

`must_match` must cover the reference's distinctive structure, not vague adjectives such as "beautiful" or "professional". Use observable statements such as "2x2 topology with narrow marginal axes" or "direct labels replace an internal legend."

## Decision contract

| Decision | Observable condition | Required action |
|---|---|---|
| `reuse` | Panel topology, mark geometry, layer topology, data encoding, and annotation/legend model all match | Reuse code; adapt data and parameters |
| `restructure` | Chart family and scientific encoding match, but one or more structural dimensions differ | Replace incompatible layout/drawing functions |
| `rewrite` | Chart family, dimensionality, mark grammar, or layer topology differs | Rebuild drawing implementation; retain only compatible data/statistics helpers |

Map the reference decision to the shared asset-adaptation vocabulary:

- `reuse` -> `exact_reuse` only;
- `restructure` -> `structural_adaptation` only;
- `rewrite` -> `style_only` when compatible visual tokens remain, otherwise `build_new`.

Do not use `style_only` to claim structural fidelity. Read `asset-adaptation.md` before selecting old code.

For `reuse`, list all five compatibility dimensions in `structural_compatibility`.

For `restructure` or `rewrite`, list concrete non-cosmetic changes in `structural_changes`. Changing only palette, colors, font, alpha, line width, or marker size is not reconstruction.

### Old-skeleton rejection (mandatory for optimization)

Optimization records must also include `composition_decision` with:

```json
{
  "old_skeleton_removed": true,
  "hero_panel": "which evidence owns visual priority",
  "support_panels": "how secondary evidence is grouped and de-emphasized"
}
```

This is a hard gate, not a prose preference. A sentence such as “replaced bars with points” does not prove redesign when the same equal-weight subplot grid, repeated axes, and detached global legend remain. If the old skeleton is retained, classify the work as a cosmetic revision and do not report it as reference-led optimization.

## Generated-script header

Put these comments before imports:

```python
# AFS-REFERENCE-DRIVEN: true
# AFS-REFERENCE-SOURCE: <path or reference id>
# AFS-REFERENCE-CONTRACT: <contract.json>
# AFS-IMPLEMENTATION-DECISION: <reuse | restructure | rewrite>
# AFS-ADAPTATION-LEVEL: <exact_reuse | structural_adaptation | style_only | build_new>
# AFS-STRUCTURAL-CHANGES: <semicolon-separated structural changes, or compatibility evidence for reuse>
# AFS-COMPARISON: <reference-vs-candidate.png>
```

After rendering, run:

```bash
python scripts/check_reference_fidelity.py generated.py \
  --contract contract.json \
  --comparison reference-vs-candidate.png \
  --reference reference.png \
  --candidate candidate.png \
  --json reference-fidelity-report.json
```

## Visual Optimization Contract

For optimize/polish/beautify/improve/redesign requests, create a second JSON record:

```json
{
  "task": "visual_optimization",
  "reference_candidates": ["one to three reviewed reference ids"],
  "opened_reference_candidates": ["ids whose pixels were opened"],
  "selected_reference": "selected id",
  "candidate_recommendation": {"request": {}, "pool": {}, "candidates": []},
  "candidate_pixel_observations": {"reference-id": "observable pixel-level grammar"},
  "selection_reason": "why this candidate best matches the required structure and evidence chain",
  "candidate_role_map": {"reference-id": ["assembly or panel roles controlled by this reference"]},
  "palette_decision": {
    "previous_palette": ["hex values or named palette from the before figure"],
    "selected_palette": "a palette-manager id, journal_baseline, or retained_explicit_colors",
    "semantic_mapping": {"role": "final color for that role"},
    "reason": "why this mapping serves the evidence and remains distinguishable at final size"
  },
  "text_contrast": {
    "applicable": true,
    "report": {"ready": true, "minimum_ratio": 4.5, "regions": [{"contrast_ratio": 4.5, "pass": true}]}
  },
  "before_diagnosis": ["observable hierarchy/layout/density/legend/legibility failures"],
  "structural_changes": ["layout, panel, geometry, layer, encoding, legend-model changes"],
  "visual_review": {
    "final_size_inspected": true,
    "hierarchy": "pass | justified_deviation",
    "panel_balance": "pass | justified_deviation",
    "whitespace": "pass | justified_deviation",
    "legend_footprint": "pass | justified_deviation",
    "text_legibility": "pass | justified_deviation"
  }
}
```

Build and validate the comparison:

```bash
python scripts/check_visual_optimization.py \
  --contract visual-optimization.json \
  --before before.png --reference reference.png --after after.png \
  --comparison before-reference-after.png --build-comparison \
  --json visual-optimization-report.json
```

For every heatmap, matrix, colored tile, or other filled mark carrying text, annotations must call `pick_text_color(cell_color)` from `scripts/palette_manager.py`; never hard-code white or another light annotation color. After export, declare each annotation bounding box in a regions JSON file, then run:

```bash
python scripts/rendered_contrast.py after.png \
  --regions text-contrast-regions.json --minimum-ratio 4.5 \
  --json rendered-contrast-report.json
```

Copy the resulting JSON payload into `text_contrast.report`. Any region below 4.5:1 blocks delivery. If the figure has no text on colored fills, set `text_contrast` to `{"applicable": false}`. `palette_decision` is mandatory for every optimization, including a justified decision to retain old colors; an omitted decision is not a default-to-old-colors path.

The checker verifies readable image evidence, authentic equal-cell composition, strict recommendation provenance, per-candidate pixel observations, selected-reference reasoning, an explicit palette decision, structural changes, final-size review, recomputed after-raster contrast, and declared physical dimensions/DPI. Candidate IDs must exactly match the recommendation report order. Static QA and self-reported fidelity items cannot replace this gate.

## Side-by-side comparison

Show the reference and candidate in equal cells. Preserve aspect ratios; do not stretch either image. Keep their order and labels in the accompanying QA record rather than overlaying labels on the evidence pixels. Inspect at the final journal width, because typography and spacing defects often disappear in enlarged previews.

Compare in this order:

1. panel topology and relative geometry;
2. marks, layers, and encodings;
3. focal hierarchy and whitespace;
4. palette roles and color proportions;
5. typography, legends, annotations, and finishing details.

Do not use pixel similarity as the gate. Different scientific data changes exact pixels. Judge whether the same visual grammar has been reconstructed while the user's evidence remains truthful.

## Rationalizations to reject

| Rationalization | Required response |
|---|---|
| "The old script is publication quality." | Quality does not establish reference compatibility. Apply the five-dimension test. |
| "Changing the palette captures the style." | Palette alone cannot reproduce layout, geometry, or layers. |
| "The chart type is roughly similar." | Rough similarity is insufficient. Classify using observable dimensions. |
| "A rewrite would take longer." | Implementation convenience ranks below a concrete reference. |
| "The data differ, so visual comparison is impossible." | Exact pixels may differ; topology, grammar, hierarchy, and roles remain comparable. |
| "The reference is only inspiration." | A user-selected concrete reference activates this protocol unless the user explicitly asks for loose inspiration. |

## Red flags — stop and reclassify

- The reference image was not opened.
- Production code was selected before the contract was written.
- `reuse` lacks evidence for all five compatibility dimensions.
- `restructure` or `rewrite` lists only color/font/alpha/linewidth/marker-size changes.
- The candidate retains panels, layers, legends, or annotations absent from the reference merely because they existed in old code.
- No equal-size comparison was inspected.
- A failed must-match item is relabeled "close enough" without a scientific, data, accessibility, or journal reason.
- Delivery claims "matches the reference" while the checker reports FIX.

Any red flag means the reconstruction is incomplete.
