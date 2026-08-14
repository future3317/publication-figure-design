# Visual Optimization Hardening Design

## Goal

Make “optimize/polish/beautify a publication figure” a reference-led structural redesign workflow that cannot pass by changing only palette, typography, alpha, line width, or spacing tokens.

## Design

The skill uses three independent gates. Source QA checks deterministic plotting baselines and exits nonzero on failure. Reference retrieval normalizes figure-type aliases and returns only reviewed examples by default; generated reconstructions remain quarantined until an explicit visual review assigns a rating. Rendered optimization QA requires real before, after, reference, and comparison images, verifies that the comparison contains the supplied images, rejects cosmetic-only change records, and requires an explicit final-size visual review record.

“Visual optimization” always activates reference-led mode, even when the user did not supply an image. The agent must query one to three compatible reviewed candidates, open their pixels, select one or document why all are structurally incompatible, then write a visual adaptation contract. Existing plotting code is treated as a data/implementation source rather than a design skeleton.

## Quality states

- `pending`: not eligible for normal retrieval; no aesthetic rating.
- `reviewed`: visually inspected against its source/goal; may have an aesthetic rating and is retrievable.
- `rejected`: retained for provenance but never offered as a normal candidate.
- `promoted`: reviewed and explicitly approved as production implementation material.

Automated generation never assigns `reviewed`, `promoted`, or an aesthetic score.

## Verification

Regression tests cover real CLI output/exit codes, taxonomy aliases, default quarantine, authentic image-comparison evidence, rejection of cosmetic-only optimization, and generated reconstruction state. The manuscript failure mode is represented by a contract with only AFS baseline/style changes and must receive `FIX`.
