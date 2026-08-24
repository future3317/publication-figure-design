# StyleSpec compilation

`StyleSpec` is the single visual-language contract shared by matplotlib, SVG, and
image-generation panels. It is compiled from a `JournalProfile`, a `StyleCapsule`, and
inspected `ReferenceDNA`, then stored with the run; renderer defaults may fill only fields
that the selected spec leaves optional.

The cross-family baseline is defined in `references/global-visual-language.md`: soft
segmentation, short title hierarchy, structural whitespace, low-saturation semantic colors,
and restrained legends/annotations. Compile those defaults into the spec before applying
reference-specific tokens; do not leave them as prose-only guidance.

## Required groups

- canvas and panel backgrounds;
- semantic palette roles and OKLCH/LAB evidence where available;
- font family, title/body/tick/annotation relative sizes, weights, and line height;
- stroke widths, marker shape/size/edge, opacity, grid/spine/tick rules;
- legend geometry, corner radius, annotation/callout/arrow treatment;
- panel gaps, whitespace rhythm, information density, and axis treatment.

## Renderer boundary

Use the shared implementations:

- `apply_style_spec_matplotlib()` for rcParams and plotting tokens;
- `apply_style_spec_svg()` for CSS/vector tokens;
- `build_image_generation_style_prompt()` for image-rich panels.

The same `StyleSpec` must be used before raster/vector composition and re-used by final
QA. A fixed palette, Arial choice, or spine/grid convention is a fallback prior only; a
concrete reference or explicit user requirement takes precedence.

## Quality versus fidelity

`reference_alignment_score`, `aesthetic_quality_score`, and
`scientific_correctness_score` are recorded separately. A high fidelity score does not
make an unattractive source an aesthetic champion, and a reconstruction preview is never
the canonical style source.
