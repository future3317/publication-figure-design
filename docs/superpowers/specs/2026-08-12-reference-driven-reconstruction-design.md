# Reference-Driven Figure Reconstruction Design

## Goal

Make an explicitly supplied or selected reference image control the figure's visual structure and language. Existing production code remains an implementation resource, never a reason to preserve an incompatible plotting skeleton.

## Problem

The current create workflow treats visual references as optional inspiration below production assets. `VISUAL ADAPT` preserves the existing script's layout, annotations, and dimensions and normally permits only palette changes. This makes small edits to an old plot the path of least resistance even when the user asks for a result that looks like a reference image. Existing tests confirm that files render and satisfy journal defaults, but they do not verify structural fidelity to a reference.

## Precedence

For reference-driven work, resolve conflicts in this order:

1. Scientific meaning, data integrity, and non-misleading encoding.
2. Explicit user requirements.
3. Reference image structure and visual language.
4. Reusable production code.
5. Skill defaults.

A reference may change layout, geometry, layering, annotation, legend, spacing, and palette. It may not falsify data, change the scientific question, or force an incompatible statistical encoding.

## Mode Routing

Add `reference-driven` as a create/revise submode. Enter it whenever the user supplies, points to, selects, or explicitly asks to imitate a reference image. Merely requesting a named palette or broad style such as "Nature style" does not activate it unless a concrete reference image is selected.

In this mode, reference retrieval is mandatory and production-asset `COPY-FIRST` priority is suspended until reconstruction planning is complete.

## Reconstruction Workflow

1. Open and inspect every selected reference image.
2. Write a Reference Reconstruction Contract before editing plotting code.
3. Classify the implementation as `reuse`, `restructure`, or `rewrite` using observable compatibility criteria.
4. Render at the target publication dimensions.
5. Create a side-by-side comparison containing the reference and candidate.
6. Complete Reference Fidelity QA. If a must-match item fails, revise and rerender.
7. Deliver the figure, code, comparison, and a concise fidelity report.

## Reference Reconstruction Contract

The contract records:

- reference identifier or path;
- scientific invariants that must not change;
- canvas aspect ratio and panel layout;
- marks and plot geometry;
- layer order and overlaps;
- axis, scale, and data encodings;
- palette roles, approximate values, and area/saturation proportions;
- typography hierarchy;
- legend and annotation design;
- whitespace, density, and focal hierarchy;
- `must_match` features;
- `may_adapt` features with data or scientific reasons;
- implementation decision and evidence.

The generated script must contain a compact machine-readable comment block for the checker. The full human-readable contract may be a companion Markdown or JSON file.

## Reuse Decision

Choose `reuse` only when all of these match the reference: panel topology, primary mark geometry, layer topology, data encoding, and annotation/legend model. Parameter changes may then adapt color, size, spacing, and labels.

Choose `restructure` when the chart family and scientific encoding match but one or more structural dimensions differ. Replace the incompatible layout or drawing functions; do not preserve them for convenience.

Choose `rewrite` when the chart family, mark grammar, dimensionality, or layer topology differs. Reusing data-loading or statistical helpers is allowed, but the drawing implementation must be rebuilt.

Changing only color, font, alpha, line width, or marker size cannot satisfy `restructure` or `rewrite`.

## Lightweight Checker

Add one dependency-free Python checker, `scripts/check_reference_fidelity.py`. It validates the process evidence rather than judging scientific similarity from raw pixels.

Inputs:

- generated plotting script;
- optional JSON contract;
- optional comparison image.

Checks:

- reference-driven marker is present;
- reference source is recorded;
- implementation decision is one of `reuse`, `restructure`, `rewrite`;
- required contract fields are non-empty;
- `must_match` is non-empty;
- structural compatibility evidence exists for `reuse`;
- `restructure`/`rewrite` includes structural changes beyond cosmetic tokens;
- fidelity review records each must-match item as pass or justified deviation;
- comparison image exists and is non-empty when a render is delivered;
- unresolved failures prevent a READY result.

The checker does not use SSIM or LPIPS. Different data legitimately changes pixels, positions, and densities; a pixel threshold would reward scientific distortion and penalize valid reconstruction.

## QA and Delivery

Add Reference Fidelity QA after normal data and publication QA:

- RF-1 reference inspected;
- RF-2 contract complete;
- RF-3 implementation decision justified;
- RF-4 layout and geometry correspond;
- RF-5 layer topology and encodings correspond;
- RF-6 palette roles and visual proportions correspond;
- RF-7 typography, annotation, legend, and spacing correspond;
- RF-8 no irrelevant old skeleton remains;
- RF-9 side-by-side comparison inspected at target size;
- RF-10 every deviation has a scientific, data, accessibility, or journal reason.

Delivery includes the normal scientific outputs plus the comparison image and Reference Fidelity Report. Never claim "matches the reference" when any must-match feature remains unresolved.

## Skill Structure

Keep `SKILL.md` as a concise router and source of hard gates. Move detailed reconstruction and QA instructions to `references/reference-driven-reconstruction.md`. Update `references/checklist.md` with the RF checks. Extend existing e2e tests rather than introducing another manager or registry.

## Testing

Use RED-GREEN-REFACTOR:

1. Run a baseline pressure scenario against the current skill and record whether the agent preserves an incompatible old skeleton.
2. Add failing unit tests for the checker.
3. Add a failing e2e scenario that rejects cosmetic-only adaptation under reference-driven mode.
4. Implement the checker and workflow instructions.
5. Repeat the same pressure scenario with the revised skill.
6. Run the focused tests, full existing Python test suite, reference integrity checks, and regression benchmark.

## Scope

Do not add image embeddings, a new asset manager, a new registry, or a new external dependency. Do not rewrite production figure assets. This change governs selection, reconstruction, evidence, and QA.
