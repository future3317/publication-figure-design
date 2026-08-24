# Figure Family Champion Board

The champion board is the quality-improvement ledger used after the compiler
architecture is frozen. It does not replace the scientific or export gates and it
does not promote a reference from metadata alone.

## Candidate loop

The current quality sprint is intentionally limited to five families declared in
`assets/reference-benchmarks/champion_board.json`:

- `statistical_discovery` (multi-panel statistical figures)
- `mechanism_architecture` (mechanism and workflow schematics)
- `matrix_array` (heatmaps and matrix figures)
- `multi_axis_comparison` (radar and other radial comparisons)
- `image_quantitative_composite` (linked image plus quantitative panels)

Other taxonomy families remain available but are not optimized or promoted by this
sprint. For each focus family, complete five real generation tasks; do not count a
placeholder, a reference-only reconstruction, or a task without a rendered candidate.

The checked-in real-paper task set is `assets/reference-benchmarks/real_generation_tasks.json`.
Run the bounded execution helper with the repository runtime:

```powershell
$env:PYTHONPATH = "E:\CODE\publication-figure-design\src;E:\CODE\publication-figure-design\scripts"
& "D:\Anaconda\envs\piepaper\python.exe" scripts/run_visual_sprint.py
```

It writes candidate renders and contact sheets under `tmp/visual_sprint/`. The helper
labels its outputs `source_render_variant`: the source paper PNG is the semantic
authority, while structure-first and style-first are deterministic visual variants.
This is valid visual evidence, but it cannot auto-promote a production champion until
a real longitudinal challenger comparison exists.

## Longitudinal visual baseline

The first 25-task run is frozen as `visual-baseline-v1` by
`scripts/freeze_visual_baseline.py`. Every later real render of the same tasks is
checked with `scripts/visual_regression.py`:

- exact matches are `unchanged`;
- changed renders require forward and reverse blind-judge payloads;
- inconsistent or missing review is `uncertain` and blocks promotion;
- the report emits wins/losses/uncertain, five-family win rates, reason-code deltas,
  and hard-QA regressions;
- the regression check never writes Champion Board promotion state.

`source_render_variant` is calibration/regression evidence only. A production
challenger must come from the same task and scientific contract after the skill
actually re-renders it.

For a representative task in a focus family:

1. Run publication mode and render the structure-first, style-first, and balanced
   candidates at final physical size.
2. Inspect the three candidates blind to their generation order. Preserve the
   before/reference/after evidence and the final QA artifacts.
3. Ask the Codex/Luna visual judge to compare the pair twice with the display order
   swapped. Store the two structured responses and accept the result only when both
   map to the same candidate. Record the resulting `preferred`/`rejected` pair and
   all three `candidate_ids` with `scripts/record_preference.py`.
4. Update the family row in `assets/reference-benchmarks/champion_board.json` only
   when the automated evidence passes: ten swapped pairwise judgments, order
   consistency ≥ 0.90, degradation detection ≥ 0.90, challenger win rate ≥ 0.60,
   scientific/L0/L1 pass, and `auto_ready=true`. L2/L3 remain useful evidence but
   are not required for `ready`.
5. Run `scripts/champion_board.py` and the normal release gate. A family with fewer
   than five reviewed tasks stays `needs_evidence`; it is not treated as a champion.

Example:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/record_preference.py candidate-a candidate-b left `
  --candidate-id candidate-a `
  --candidate-id candidate-b `
  --candidate-id candidate-c `
  --task-id grouped_bar_01 `
  --figure-family comparison_effect `
  --reason-code hierarchy `
  --reason-code spacing `
  --reviewer auto_visual_judge
& "D:\Anaconda\envs\piepaper\python.exe" scripts/champion_board.py --output tmp/champion-board.json
```

The preference record keeps `left/right/winner` for benchmark readers and also writes
the canonical `preferred/rejected/reason_codes` fields. Use only these eight reason
codes: `layout`, `hierarchy`, `spacing`, `typography`, `palette`, `annotation`,
`data_clarity`, and `overall_polish`. Put any one-off explanation in `notes` instead
of expanding the taxonomy.

## Board fields

Each family records:

- `champion`, `challenger`, and `last_release` for generated tasks;
- optional `reference_upper_bound` for a strong visual reference that is not a generated
  champion;
- blind-judge preference win rate and reason-code counts;
- scientific pass, L0/L1/L2/L3, and repair iterations;
- reference coverage, quality, diversity, and their product (diagnostic only);
- explicit gaps for annotation grammar, topology, dense/sparse density, journal/profile,
  palette roles, direct-label/legendless layouts, asymmetric heroes, and mixed
  image-plus-quantitative panels.

`challenger_win_rate`, `scientific_pass`, `mean_repair_iterations`,
`judge_order_consistency`, and `degradation_detection_rate` are the operating KPIs.
A focus family becomes `ready` only with at least five generation tasks, five accepted
three-candidate records, ten swapped pairwise judgments, order consistency and
degradation detection ≥ 0.90, challenger win rate ≥ 0.60, scientific/L0/L1 pass, and
`auto_ready=true`. L2/L3 and `coverage × quality × diversity` remain diagnostic; they
cannot make up for failed calibration. An inconsistent pair is uncertain and never
enters the champion board.
