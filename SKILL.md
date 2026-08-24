---
name: publication-figure-design
description: "Use when creating, reconstructing, revising, reviewing, or exporting publication-grade scientific figures for Nature/Cell/Science-family manuscripts, especially when a concrete visual reference, multi-panel layout, paired operating-point comparison, uncertainty-aware chart, or final-size visual QA is involved."
---

# Publication Figure Design

This skill is an orchestrated, reference-first Scientific Figure Design Compiler. Scientific meaning, complete data
take precedence over visual similarity; uncertainty semantics and a concrete reference control the
visual grammar; generic defaults are fallback-only.
Scientific meaning, complete data are never overridden by a visual reference.
The contract is explicit: scientific meaning, complete data remain authoritative.
A visual reference never changes scientific semantics; it only supplies visual grammar.

## Operating contract

Read `references/orchestrator-contracts.md` and run the orchestrator for every create,
revise, optimize, reference-intake, review, or export task. The orchestrator persists
machine-readable artifacts; do not rely on context memory or prose claims.

Required state sequence:

`Route → Intake → Reference Retrieval → Reference Inspection → Design Spec → Binding → Render → Compare → Critique → Repair → QA → Export`

Each transition has a gate. A failed gate blocks the next state and produces a repairable
report. Resume, retry, rollback, and best-so-far are explicit operations in the run state.

Core artifacts:

`TaskSpec`, `SourceSpec`, `TargetSpec`, `ReferenceSet`, `LayoutSpec`, `StyleSpec`,
`TypographySpec`, `PaletteSpec`, `ComponentSpec`, `BindingMap`, `RenderPlan`, `QAReport`,
`ExportManifest`.

Use the unified CLI when available:

```text
pfd run <task-spec>
pfd reference ingest <image>
pfd reference analyze <reference-id>
pfd reference review <reference-id>
pfd reference benchmark <reference-id> <canary.json>
pfd reference promote <reference-id> <champion-evidence.json>
pfd index build
pfd eval quick|full|visual|release
```

Run all Python commands through the repository runtime convention in
`references/runtime-environment.md`: use the `piepaper` Conda environment and never
silently fall back to Conda `base` or system Python.

Every persisted session records `input_hash`, the concrete reference-index version,
selected reference ids, renderer version, iteration history, QA result, and final output
hash. Resume must reuse the recorded selection; it must not rerun an unseeded recommendation.

`manifest.yaml` treats `always_load` and route `required_load` as mandatory, and separates
them from optional `load`: at route entry, read every required resource before proceeding;
a missing or unread required resource blocks Render/QA/Export. Ordinary `load` entries are
supplemental and may be consulted when the task needs them.

The compiler path is:

`ScientificContract → ReferenceDNA → StyleCapsule + JournalProfile → DesignPacket → CandidateSet → DesignPatch → RenderTrace → layered QA → ExportManifest`.

Reference intelligence is source-specific: raster, SVG, PDF and plotting code use separate
analyzers. Raster evidence records only font class and relative hierarchy; exact font and stroke
values require vector or static-code evidence. The active index is a transparent hybrid index
(metadata + semantic + structure + StyleDNA + task compatibility), not a metadata proxy.
Use `reference_dna.json`, `profiles/style-capsules/`, and `profiles/journals/` as the current
sources of truth.

## Global visual language

Apply the baseline in `references/global-visual-language.md` to every figure family unless
scientific semantics, an explicit user requirement, journal constraints, or an inspected
concrete reference require a documented deviation:

- **soft segmentation:** use whitespace, alignment, subtle tonal shifts, or thin separators;
  avoid heavy boxes and dashboard-like grids.
- **short title hierarchy:** use concise evidence-job titles with a visible title/body/tick/
  annotation size order; move explanations into labels or captions.
- **whitespace is structural:** preserve margins, gutters, label clearance, and breathing room;
  do not fill empty space just to increase visual density.
- **low-saturation semantic colors:** use stable role-based colors with restrained chroma and
  sparse accents; low saturation must not reduce text, stroke, or critical-mark contrast.
- **restrained legends and annotations:** prefer direct labels when useful, otherwise one compact
  legend; annotate only claim-bearing events, thresholds, uncertainty, or exceptions.

These are compiled into `LayoutSpec`, `TypographySpec`, `PaletteSpec`, and `ComponentSpec`;
they are not a prose-only aesthetic suggestion and must not be replaced by backend defaults.

### Scientific figure-design principles

The global rules also contain the mandatory scientific design layer. Run the
**figure-versus-table preflight** before choosing a chart: reserve figures for patterns,
geometry, distributions, mechanisms, spatial structure, and continuous relationships;
keep exact scalar results, mean ± SD, benchmarks, ablations, latency, memory, and
small categorical comparisons in tables when a table preserves nearly all information.
Choose the family from data semantics, then **visualize model outputs, not only metrics**.
Preserve the mathematical domain and actual data; **do not invent or exaggerate scientific effects**
or change a shared mean, camera, scale, or uncertainty representation for drama.

For qualitative comparisons, hold the **same sample, camera, crop, scale** and all other
controlled factors fixed: **one visual variable per experimental variable**. Keep color
roles stable across the paper, but let structure and actual outputs—not recoloring—carry
the method difference. A **main figure answers one scientific question** and normally uses
1–3 meaningful panels with a dominant evidence panel rather than a dashboard grid. The
**caption carries the explanation**; figure text stays short and claim-bearing.

The semantic family decision, mathematical-domain check, comparison-control check,
object/uncertainty attachment check, and cross-figure color-role check **must run before rendering**.
Record the results in `TaskSpec` or `DesignPacket`; a failed preflight blocks
Render until the contract is repaired.

## Dispatch

Route the request before touching plotting code. The supported modes are **create**,
**revise**, **review**, **export**, and **reference**. Create uses the complete state
machine; revise and review run only affected creation stages; export runs QA/export
stages; reference runs intake/analysis/reproduction checks. Do not force revise, review,
export, or reference work through a full create pipeline. Do not use generic `query()` for
optimization retrieval.
Do not force revise, review, export, or reference work through a full pipeline.

### Mandatory visual-optimization route

For an existing-figure optimization, use the mandatory low-freedom route:
`scripts/prepare_visual_optimization.py` → `scripts/check_visual_optimization.py`.
The preparation script internally runs `reference_library.py recommend`; do not call a
second generic `query()` or duplicate recommendation step. Do not edit plotting source
until the packet records the selected candidates, the pixel observations, and the
structural diagnosis. Preserve a `Before | Reference | After` evidence set, and treat
Palette/font/alpha/line-width/marker-size/spacing-only changes as cosmetic-only unless
the packet also records a structural, encoding, or legend-model repair.

### Concrete-reference gate

When a concrete reference exists, inspect all five dimensions—layout, visual grammar,
palette, typography, and annotation/component details—at final display size before
selecting implementation material. A visual reference never changes scientific
meaning, complete data, variable roles, or uncertainty semantics. The production figure
must preserve those semantics even when the visual language is adapted.

Optional reference library use is for style discovery and auditable reconstruction. It
is not a substitute for opening the selected pixels. Use at most 3 candidates per role,
record their image hash and observations, then choose structure and style independently.

Backend choice is resolved by `references/backend-selection.md`: explicit request,
workflow requirement, saved preference, then the Python default. Mixed panels require
one final assembler and an explicit request or real capability need; never silently
substitute a backend.

The reference-fidelity route also runs `scripts/check_reference_fidelity.py` and records
all five dimensions before production asset selection.

### Reference quarantine and production eligibility

Every newly ingested image starts at `raw` and advances only through
`analyzed → reviewed → benchmarked → production`. `query` may show reviewed items for
diagnostics, but formal recommendation must use `--require-benchmark` or an equivalent
production route. A reference enters the recommendation pool only after a passing
retrieval/generation canary; promotion additionally requires champion-floor evidence.
Legacy sidecars without `lifecycle_state` remain readable but are reported by
`scripts/check_reference_quarantine.py` for migration.

Reference-local `code.py` is never executed during intake. If an explicitly requested
private audit must run one, use `scripts/reference_code_sandbox.py`; it rejects network,
process, and unknown imports, runs in a temporary working directory with a timeout, and
records the exception in the audit artifact.

## Reference-first rules

When a concrete image is supplied or selected:

1. Open every concrete reference at final display size; inspect its actual pixels before
   you select implementation material. Select implementation material only after inspection.
2. Retrieve roles separately: `structure_reference`, `style_reference`,
   `component_references`, `annotation_reference`, and optional `palette_reference`.
3. Compile the selected pixels into `LayoutSpec` and `StyleSpec`; do not ask the agent to
   infer style informally.
4. Bind every target element as `match`, `restructure`, `rewrite`, `omit`, or `add`.
5. Render at final physical dimensions, compare the final raster/vector to the reference,
   then critique and repair only the highest-impact failures.

The adaptation levels are `exact_reuse`, `structural_adaptation`, `style_only`, and
`build_new`. `exact_reuse` requires matching panel topology, mark geometry, layer topology,
data encoding, and annotation/legend model. Every render plan declares its backend and final assembler.

Generation modes are `fast` (one draft), `standard` (up to two drafts), and `publication`
(structure-first, style-first, balanced low-cost candidates before final render). Critique emits
machine-editable `DesignPatch` operations; Repair applies them deterministically. Renderers also
emit `RenderTrace` so scientific QA can inspect data → transform/statistic → graphical mark.

`quality` and `fidelity` are independent. A faithful but unattractive reference may be a
valid structure source but must not become an aesthetic champion. A reconstruction is a
validation artifact, never the canonical style source.

## Gates that block delivery

- scientific correctness and data/provenance completeness;
- reference alignment measured from the final image, not declarations;
- typography, contrast, color accessibility, layout, legend, and annotation legibility;
- reproducible render plan and fixed seed/runtime where synthetic data is used;
- vector/raster dimensions, DPI, font substitution, and export manifest;
- L0 hard technical, L1 scientific, L2 structural visual, and L3 soft perceptual QA as separate artifacts;
- anti-copy checks that permit style logic but block copied scientific content, labels, unique assets, and near-identical placement;
- provenance and allowed reuse scope for every reference/template/source asset.

Benchmark delivery is a hard gate, not an informational score. CI enforces Recall@1 ≥ 0.90,
Recall@3 ≥ 0.97, NDCG@3 ≥ 0.95, mean alignment ≥ 0.7771, per-dimension structure,
composition, whitespace, typography, palette roles, marks/strokes, annotations, density,
and overall-style floors, scientific correctness = 100%, export contract = 100%, and zero
champion regression. Development/validation/holdout splits, adversarial retrieval cases,
the 20-task generation-regression corpus, scale checks (100/500/1,000/5,000 references),
and adapter canaries are separate gates.

Visual quality improvement is evidence-led after the architecture is frozen. The active
sprint is limited to five families in `champion_board.json` (`statistical_discovery`,
`mechanism_architecture`, `matrix_array`, `multi_axis_comparison`, and
`image_quantitative_composite`); other taxonomy families retain their current evidence
state. For each focus family, publication mode renders exactly three candidates
(structure-first, style-first, balanced). The Codex/Luna visual judge compares the
candidate pair twice with the display order swapped; only an order-consistent structured
response is accepted, and uncertain pairs are discarded. `scripts/auto_visual_judge.py`
validates this protocol and calibration on known original/degraded pairs. A focus family
is `ready` only after five real generation tasks, five accepted three-candidate records,
ten swapped pairwise judgments, order consistency ≥0.90, degradation detection ≥0.90,
challenger win rate ≥0.60, scientific/L0/L1 pass, and `auto_ready=true`. The sprint
hard-stops at three candidates, one repair, and two judge rounds (forward plus reverse);
an uncertain result keeps the current champion. L2/L3 remain diagnostic evidence. A
reference upper bound is never a generated champion.

To execute the real-paper sprint, use `scripts/run_visual_sprint.py` with
`assets/reference-benchmarks/real_generation_tasks.json`. It renders exactly 25
source-backed tasks (five per focus family), writes the 75 candidate PNGs and
family contact sheets under `tmp/visual_sprint/`, runs the swapped judge and
degradation calibration, and records measured evidence on the Champion Board. Its
candidate method is explicitly `source_render_variant`: the paper PNG is the
semantic authority and the two alternatives are deterministic visual variants;
this evidence does not auto-promote a production champion without a longitudinal
challenger comparison.

The current sprint is frozen as `visual-baseline-v1` in
`assets/reference-benchmarks/visual-baseline-v1.json`. Freeze it with
`scripts/freeze_visual_baseline.py`; subsequent real renders are compared with
`scripts/visual_regression.py`. Exact matches are unchanged. A changed render must
provide forward/reverse blind-judge JSON; missing or inconsistent review is
`uncertain` and blocks promotion. This regression path reports wins/losses/uncertain,
family win rates, reason-code deltas, and hard-QA regressions, but never changes the
Champion Board by itself.
Never overwrite a frozen baseline during ordinary development. After a passing
longitudinal comparison, create the next checkpoint by passing an output such as
`assets/reference-benchmarks/visual-baseline-v2.json`; the freezer derives the matching
image directory and rejects existing checkpoints unless `--replace` is explicit.

Reference-led renderers must explicitly consume `TypographySpec`, `PaletteSpec`,
`LayoutSpec`, and `ComponentSpec` through `scripts/render_contract.py`. A renderer may not
silently replace those tokens with backend defaults or report production-ready output
without the final QA/export artifacts.

Run the relevant checks from `manifest.yaml`; for skill maintenance also run
`scripts/check_skill_contract.py`, `scripts/check_source_reference_catalog.py`, the
package tests, and the reference/index checks.
Use `pfd eval quick|full|visual|release`; `release` is the same gate as CI.

## Resource routing

| Need | Read or run |
|---|---|
| Orchestration and artifact schemas | `references/orchestrator-contracts.md`, `src/publication_figure_design/contracts/`, `src/publication_figure_design/orchestrator/runtime.py` |
| Global visual language | `references/global-visual-language.md` |
| Concrete reference or optimization | `references/reference-driven-reconstruction.md`, `scripts/compare_output_to_reference.py` |
| Style compilation | `references/style-spec.md`, `scripts/style_compiler.py` |
| Reference intake/library | `references/visual-reference-library.md`, `references/color-palettes.md`, `scripts/reference_library.py`, `scripts/check_references.py --require-previews` |
| Reference DNA and hybrid retrieval | `src/publication_figure_design/reference_intelligence/`, `scripts/build_reference_dna.py`, `scripts/build_reference_indexes.py` |
| Journal profiles and style capsules | `profiles/journals/`, `profiles/style-capsules/`, `src/publication_figure_design/style/` |
| Design compiler and patches | `src/publication_figure_design/design/`, `src/publication_figure_design/layout/` |
| Art direction and visual grammar | `references/art-direction.md`, `references/visual-grammar.md` |
| Asset adaptation and reuse | `references/asset-adaptation.md`, `references/figure-legend-contract.md`, `references/privacy-provenance.md` |
| Figure-family or backend choice | `references/figure-family-coverage.md`, `references/backend-selection.md` |
| Journal target and physical sizing | `references/journal-specs.md`, `references/export-specs.md` |
| Scientific encoding/uncertainty | `references/encoding-and-uncertainty.md` |
| QA/export | `references/checklist.md`, `references/delivery-contract.md`, `references/export-specs.md`, `scripts/rendered_contrast.py`, `scripts/audit_pdf_text.py` |
| Layered QA and trace | `src/publication_figure_design/qa/`, `RenderTrace`, `scripts/render_contract.py` |
| Source reconstruction maintenance | `references/source-reconstruction-library.md`, `scripts/check_source_reconstruction_library.py`, `scripts/check_source_reference_catalog.py` |
| Optimization packet | `scripts/prepare_visual_optimization.py`, `scripts/check_visual_optimization.py` |
| Benchmark and release gates | `scripts/ci_gate.py`, `scripts/evaluate_benchmark.py`, `scripts/evaluate_holdout.py`, `scripts/evaluate_generation_regression.py`, `scripts/check_champion_floors.py`, `scripts/adversarial_retrieval.py`, `scripts/scale_benchmark.py` |
| Champion board and preference evidence | `references/champion-board.md`, `assets/reference-benchmarks/champion_board.json`, `assets/reference-benchmarks/real_generation_tasks.json`, `assets/reference-benchmarks/visual-baseline-v1.json`, `scripts/champion_board.py`, `scripts/run_visual_sprint.py`, `scripts/freeze_visual_baseline.py`, `scripts/visual_regression.py`, `scripts/record_preference.py`, `scripts/auto_visual_judge.py` |
| Quarantine and sandbox | `scripts/check_reference_quarantine.py`, `scripts/migrate_reference_quarantine.py`, `scripts/reference_code_sandbox.py`, `scripts/render_contract.py` |

Do not execute untrusted reference-local code as part of intake. Prefer the constrained
renderer/spec compiler path; if a legacy reproduction script is needed for a private,
trusted asset, record that exception in the run artifact and keep it outside production
retrieval.
