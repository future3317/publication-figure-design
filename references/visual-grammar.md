# Visual Grammar Observation Card

Use this card after opening a concrete reference at its actual pixels and before
writing or changing rendering code. It turns visible choices into implementation
constraints. It is not a catalogue of decorative options: a family is either
described at the level needed to redraw it or written exactly as `not_present`.

The card belongs in `reference_visual_grammar` for a reconstruction and
`selected_reference_visual_grammar` for visual optimization. Its `must_match`
items must also appear in the reconstruction contract's top-level `must_match`.

```json
{
  "canvas_composition": {
    "aspect_and_panel_layout": "...",
    "visual_hierarchy": "...",
    "alignment_and_spacing": "..."
  },
  "connectors": "not_present | { geometry, direction_and_arrowhead, stroke, anchors_and_routing, layering }",
  "objects_material": "not_present | { shape_and_projection, fill_and_material, outline_and_edges, depth_cues, placement_and_scale }",
  "repetition_structures": "not_present | { topology, count_spacing_rhythm, grouping_and_alignment, variation_and_emphasis }",
  "palette_roles": {
    "background": "...",
    "roles_and_proportions": "...",
    "contrast_and_emphasis": "..."
  },
  "annotations_typography": {
    "text_hierarchy": "...",
    "callouts_and_leaders": "...",
    "placement_and_clearance": "..."
  },
  "legend_key": "not_present | { scope, placement, entries_and_encoding, frame_treatment }",
  "chart_marks_axes": "not_present | { marks_and_encoding, axes_and_scales, guides_and_grid }",
  "must_match": ["observable feature ..."]
}
```

## How to observe

Write what is visible, relational, and drawable. Avoid labels such as "nice",
"clean", "Nature-like", or a bare hex palette: they do not tell a renderer what
to draw.

| Family | Record when present |
|---|---|
| Canvas | Aspect ratio; panel sequence and relative size; dominant focal element; baselines, gutters, and intentional whitespace. |
| Connectors | Straight, curved, or orthogonal path; direction and arrowhead; color role and relative width; where it leaves and arrives; whether it passes behind objects or labels. |
| Objects/material | Shape and projection; flat/gradient/texture fill; outline treatment; highlight, shadow, and occlusion; relative scale and placement. |
| Repetition | Row, stack, branch, matrix, or pipeline; count and spacing rhythm; shared baseline/container; which repeat is emphasized or varied. |
| Palette | Background and neutral context; evidence, comparison, and accent roles; their approximate visual share; contrast hierarchy. |
| Annotations | Label hierarchy; direct labels, leaders, brackets, or callouts; anchors and clearance from marks. |
| Legend/key | Whether it exists; global/local/direct-label scope; position relative to data; entry encoding and frame treatment. |
| Chart system | Mark geometry and channel mapping; axis/scales/ticks; guide/grid prominence. |

`not_present` is evidence, not an empty convenience field. For example, a
mechanism schematic with no legend must say `"legend_key": "not_present"`; a
scatter plot with no arrows must say `"connectors": "not_present"`. Do not invent
3D material, connector arrows, or legends because another reference used them.

## From card to code

Every `must_match` item must be checked after rendering. Translate the remaining
observations into explicit drawing decisions before implementation: connector
observations choose the path/arrow/linewidth/z-order API; material observations
choose patches, gradients, highlights, outlines and occlusion order; repetition
observations choose layout primitives and spacing; legend observations decide
whether to reserve key space, direct-label, or omit the legend.

For the bundled dispersion-style mechanism example, a useful card says: a wide
left-to-right explanatory sequence; sparse muted purple/red curved connectors
with small terminal arrowheads; overlapping sphere-like forms with restrained
highlights and dark outlines; local labels in open whitespace; and no legend or
axes. "Purple and red arrows" alone is insufficient because it loses curvature,
weight, anchoring, and layer order.

## Review rule

Render at final size, compare reference and candidate, then mark each
`must_match` feature `pass` or `justified_deviation`. A deviation needs a
scientific, data, accessibility, or venue reason. Do not use pixel similarity to
excuse a missing connector route, flat object material, collapsed repetition
rhythm, or an invented legend.
