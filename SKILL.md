---
name: publication-figure-design
description: "Use when creating, reconstructing, revising, reviewing, or exporting publication-grade scientific figures across research fields and venues, especially with references, multi-panel layouts, uncertainty, or final-size QA."
---

# Publication Figure Design

Use this skill for publication figures in any research domain. The orchestrator supplies the task route and compiled policy; this file gives the agent the short working contract.

## Non-negotiable contract

- The scientific brief and complete source data control meaning, labels, variable roles, statistics, and uncertainty. A reference controls visual grammar only.
- Run the task through `pfd run <task-spec>` and follow the persisted `RoutePlan` in its output. Do not manually expand the workflow or skip a gated stage.
- Use the returned `PolicyPacket` and concrete QA feedback. Validators enforce hard constraints; do not load all `rules/*.yaml` into the prompt.
- Production starts with one candidate. The explicit evaluation route may request three. Failed create/revise QA inserts at most one critique -> repair -> render -> QA cycle; Critique pauses for an agent `DesignPatch`, then resume. Review/export QA failures report and block without forcing rendering.
- Inspect selected reference pixels before implementation. Select structure, style, palette, and component evidence independently when each is needed; never copy a reference's scientific content.
- Final QA must cover scientific meaning, readability, visual clarity, accessibility, the requested export contract, and a final-size visual inspection before delivery.

## House visual language

Apply these defaults unless scientific meaning, an explicit user request, journal requirements, or inspected evidence requires a reasoned exception:

- Use soft segmentation: separate regions with alignment, whitespace, subtle tonal shifts, or thin rules; avoid heavy boxes and dashboard grids.
- Use short, evidence-led titles with a clear title, label, tick, and annotation hierarchy.
- Treat margins, gutters, and label clearance as part of the layout. Do not fill open space without a communication reason.
- Use low-saturation role-based colors with sparse accents. Maintain strong contrast for text and important marks.
- Keep legends compact; use direct labels when they reduce decoding effort. Annotate only meaningful events, thresholds, uncertainty, or exceptions.
- Make every panel, arrow, mark, interval, and annotation serve a readable scientific story; preserve correct geometry and avoid collisions, clipping, and decorative noise.

## Route-specific behavior

- **Create:** establish the scientific contract, choose a suitable figure family and backend, then render and QA.
- **Revise:** inspect the existing output, diagnose its highest-impact structural problems, then repair and QA only affected parts.
- **Review:** inspect the supplied figure and run applicable QA without forcing design or render stages.
- **Export:** run delivery and export checks for the existing artifact.
- **Reference intake:** analyze and validate supplied reference assets through the reference lifecycle; reference-local code is not run during intake.
- A supplied reference conditionally adds retrieval, pixel inspection, and comparison stages to create/revise. Failed create/revise QA conditionally inserts the single repair cycle; review/export failures report and block without forcing rendering.

When a concrete reference is supplied, compare layout, visual grammar, palette, typography, and annotation/component choices at final display size. Record what to match, restructure, rewrite, omit, or add before editing source. Cosmetic-only adjustments do not count as a structural repair when layout, encoding, or legend behavior is defective.

For an existing-figure optimization, run `scripts/prepare_visual_optimization.py` and inspect its evidence packet before editing plotting source; run `scripts/check_visual_optimization.py` on the result.

Choose a backend by explicit request, workflow need, saved preference, then the Python default. Mixed backends require a concrete capability reason and one final assembler; never substitute silently.

When the `tex_backend` route selects TeX/TikZ/PGFPlots, read `references/tex-rendering.md`, declare the engine and package versions, inspect compiler output and PDF fonts, check overfull boxes and final page dimensions, and review a PNG rendered at the intended physical size. Missing TeX support blocks that backend; it does not silently switch backends.

## Runtime and maintenance

Use the repository's `piepaper` interpreter from `references/runtime-environment.md`; never use Conda `base` or unrelated system Python. For reference intake, source reconstruction, benchmark, and champion maintenance, use the dedicated commands and validation gates listed in `docs/maintenance/runtime-and-evaluation.md`. Those development/evaluation policies are not part of ordinary figure generation.
