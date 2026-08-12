# Reference-driven baseline (RED)

Observed against the pre-change `SKILL.md` at commit `aa6eb0f`.

## Pressure scenario

The user supplies a concrete reference image whose layout is a 2x2 compound plot with marginal distributions, plus an existing single-axis scatter script. They ask Codex to make the output look like the reference and mention that reusing the old script would be faster.

## Existing instructions that permit the failure

- Step 4.5 calls visual-reference retrieval "optional".
- References are limited to "visual language" after production assets are selected.
- `VISUAL ADAPT` says to preserve the production asset's layout, dimensions, annotations, and export parameters.
- A reference with an adaptable palette may replace the color list "while keeping everything else unchanged."
- Existing QA checks publication defaults and whether a PNG renders, not whether the reference's panel topology, mark grammar, or layer topology was reconstructed.

## Failing behavior

An agent can keep the single-axis scatter skeleton, replace its palette/font/line widths, cite the compound reference as inspiration, and pass the current automated checks. The result is a cosmetic adaptation, not a reconstruction. This is the behavior the new S6 e2e scenario and fidelity checker must reject.

