# Art Direction for Publication Figures

Choose one direction for a mechanism schematic, architecture diagram, image-rich plate,
or non-trivial multi-panel figure. It controls hierarchy, composition, visual material,
and annotation voice; it never changes data relationships or statistical encoding. Do not
blend directions unless the contract declares distinct panel roles. For a simple single
quantitative plot, use `analytic_minimalism` without decorative illustration.

## `hero_illustration`

Use for one central mechanism, geometry, material, cell, device, or model that benefits
from a memorable visual object.

- Build around one dominant illustrated object or scene; put labels and short explanatory
  steps around it, not inside a field of repeated boxes.
- Use depth sparingly: soft translucent volume, a restrained gradient, or one cutaway is
  enough. Limit accent colors to semantic forces or states.
- Make causal direction readable by spatial progression and a few deliberate connectors.
- Avoid dashboard grids, arrow soup, equal-weight clip-art, and decorative texture that
  obscures the mechanism.

## `editorial_evidence_chain`

Use for Figure 1 or a multi-panel overview that must read as a coherent scientific story.

- Give one result, image, or mechanism panel the largest visual share; arrange compact
  support panels in reading order around it.
- Reuse one alignment rhythm, one annotation voice, and one accent for the claim.
- Let evidence advance from context to mechanism to validation instead of making every
  panel compete equally.
- Avoid an undifferentiated 2×2/3×2 grid, repeated legends, and a title card that carries
  more visual weight than the evidence.

## `modular_blueprint`

Use for computational architecture, experimental workflow, or dataflow whose logic is
best expressed as precise modules and links.

- Use a strict grid, a small set of module shapes, orthogonal connectors, and one clear
  reading direction.
- Reserve color for subsystem identity or state; use neutral containers and direct labels.
- Show transformations at boundaries, not inside every module.
- Avoid pseudo-3D blocks, dense crossing arrows, and unrelated pictograms.

## `specimen_evidence_atlas`

Use when microscopy, spatial maps, specimen images, or experimental exemplars are primary
evidence rather than decoration.

- Let images occupy meaningful area at matched scale; provide scale bars and concise
  panel-local labels.
- Pair the image plate with only the quantitative panel needed to validate what is seen.
- Use borders, crops, and color keys consistently so comparisons are immediate.
- Avoid thumbnail walls, inconsistent crops, or forcing images into a generic chart grid.

## `analytic_minimalism`

Use for plot-led results, ablations, benchmarks, and supplemental quantitative figures.

- Let marks and direct labels carry the argument; use generous whitespace, low-ink axes,
  one stable semantic palette, and a compact legend or direct labeling.
- Make one comparison dominant through scale, placement, or emphasis rather than effects.
- Avoid decorative gradients, illustrative icons, heavy boxes, and unnecessary visual
  metaphors.

## `comparative_storyboard`

Use for before/after, intervention, treatment-response, or staged process comparisons.

- Set up a fixed visual anchor, then show two to four ordered states with the same spatial
  scale and stable color/marker meaning.
- Put the change at the transition; use short captions and only the connectors required
  to make order unambiguous.
- Pair the scene sequence with one outcome panel when quantitative confirmation matters.
- Avoid retelling the same step in text, legend, arrows, and repeated panels.

## Selection rule

Record `art_direction.id` and why it serves the claim in the optimization contract. A
concrete reference may demonstrate a direction, but copy only its observable grammar.
If the reference and the requested evidence call for different directions, keep the
scientific evidence and select a compatible direction rather than forcing a visual match.
