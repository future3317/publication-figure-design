# Publication Figure Design

Reference-first scientific figure design for publication workflows. This repository
contains the current `publication-figure-design` Codex Skill: an orchestrated compiler
that turns a scientific contract and visual evidence into a reproducible, QA-gated
figure package.

A reference provides visual grammar only. It never changes the target figure's data
meaning, statistical transform, uncertainty semantics, labels, or variable roles.

## Repository contents

- [`SKILL.md`](SKILL.md) is the thin agent entrypoint; [`manifest.yaml`](manifest.yaml)
  defines routes and validation commands.
- [`src/publication_figure_design/`](src/publication_figure_design/) is the production
  runtime: contracts, reference intelligence, style compilation, layout, renderers,
  orchestration, and layered QA.
- [`assets/`](assets/) contains maintained figure assets and the reference corpus,
  including metadata, `ReferenceDNA`, reproduction material, previews, and provenance.
  `ReferenceDNA` now includes a scientific-semantics layer: claim type, encoding
  rationale, pedagogy, caption requirements, and accessibility evidence, so retrieval
  is driven by *why* a reference works, not only its visual appearance.
- [`profiles/`](profiles/) and [`indexes/`](indexes/) contain journal/style profiles,
  deterministic hybrid retrieval indexes, and **domain profiles** that change the
  semantic contract for a field (`ml-ai`, `biomedical`, `genomics`, `microscopy`,
  `chemistry-materials`, `systematic-review`) rather than acting as skin swaps.
- [`scripts/`](scripts/) and [`evals/`](evals/) contain maintenance commands and the
  executable evaluation/release gates. The output eval suite now covers adversarial
  mutations, semantic correctness, statistical integrity, visual clarity,
  accessibility, publication compliance, export integrity, and reference selection.
- [`rules/`](rules/) is the machine-readable rule source, while
  [`sources/registry.yaml`](sources/registry.yaml) records rule provenance. Each rule
  now carries an `authority` level (`scientific_integrity`, `publisher_requirement`,
  `accessibility`, `evidence_based_guidance`, `house_style`, `heuristic`) and a
  rationale. Global scientific/accessibility invariants are separate from house
  defaults, family rules, journal profiles, and backend implementation details.
- [`assets/anti-pattern-atlas/`](assets/anti-pattern-atlas/) pairs bad figures with
  diagnosis and corrected counterparts.

## Runtime lifecycle

All create, revise, review, export, optimization, and reference-intake tasks use the
same persisted route:

```text
Route → Intake → Reference Retrieval → Reference Inspection
      → Design Spec → Binding → Render → Compare → Critique
      → Repair → QA → Export
```

Sessions record the selected references, concrete index version, renderer/style
versions, iterations, QA artifacts, and output manifest. Resume reuses the recorded
selection rather than silently re-ranking references.

Retrieval is role-separated (`structure`, `style`, `palette`, `component`, and
`annotation`). Selected pixels are inspected before implementation material is chosen
and compiled into `ReferenceDNA → StyleCapsule + JournalProfile → DesignPacket`.
Publication mode renders structure-first, style-first, and balanced candidates before
the final repair and export decision.

## TeX backend

TeX/TikZ/PGFPlots is a first-class backend for native vector geometry, manuscript-matched
fonts, and editable PDF output. Read [`references/tex-rendering.md`](references/tex-rendering.md),
declare the engine/package compatibility and final assembler, and carry compile logs,
font embedding, overfull-box, page-geometry, and final-size PNG evidence into QA. If the
TeX capability is missing, stop that route rather than silently switching to Python/R.

### Reading contract

`manifest.yaml` separates reading from machine rules: `always_load` is required for every
task, a route's `required_load` must be read when entering that route, and ordinary
`load` entries are supplemental reading. `always_rulesets` and `required_rulesets` are
compiled before rendering and are not optional reading. A route may not proceed to
Render, QA, or Export until its required material is available and read. The contract is checked by
[`scripts/check_skill_contract.py`](scripts/check_skill_contract.py).

Validate rules and source provenance with:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_rule_contract.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_journal_profiles.py
```

## Quick start

Use the dedicated `piepaper` environment. On the maintainer workstation:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" -m pip install -e .
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli run <task-spec.json>
```

Useful commands:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli reference ingest <image>
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli reference analyze <reference-id>
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli index build
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli eval quick
& "D:\Anaconda\envs\piepaper\python.exe" scripts/champion_board.py --output tmp/champion-board.json
& "D:\Anaconda\envs\piepaper\python.exe" scripts/ci_gate.py
```

Do not use Conda `base`, a bare system `python`, or an unrelated environment. Optional
dependencies are declared in [`pyproject.toml`](pyproject.toml) and belong in
`piepaper` only when the selected route needs them.

## Reference library contract

New references advance through:

```text
raw → analyzed → reviewed → benchmarked → production
```

Production references need metadata, source-appropriate analysis, reproducible
reconstruction/reproduction material, a preview, provenance, and passing canaries.
Reference-local `code.py` is never executed during intake; an explicitly requested
private audit uses the constrained [`scripts/reference_code_sandbox.py`](scripts/reference_code_sandbox.py).

The index is transparent and versioned. `current` is only an alias; the concrete index
record retains the corpus, schema, model, and build identity needed to reproduce a
past selection.

## Quality gates

[`scripts/ci_gate.py`](scripts/ci_gate.py) is the merge/release gate. It covers unit and
package tests, reference validation and reconstruction/fidelity checks, DNA/index
checks, benchmark/holdout/adversarial/scale evaluation, generation regression,
champion floors, quarantine, adapter canaries, and the orchestrator lifecycle canary.

Figure QA remains layered:

- **L0** technical/export contract;
- **L1** scientific correctness and provenance;
- **L2** structural visual alignment;
- **L3** perceptual quality, typography, contrast, density, and finish.

Reference-led renderers must consume `TypographySpec`, `PaletteSpec`, `LayoutSpec`, and
`ComponentSpec`; visual similarity cannot override scientific or export failures.

After the architecture is frozen, the quality sprint is deliberately limited to five
focus families: `statistical_discovery`, `mechanism_architecture`, `matrix_array`,
`multi_axis_comparison`, and `image_quantitative_composite`. Each real task produces
exactly three publication candidates (structure-first, style-first, balanced). The
Codex/Luna visual judge compares the candidates with the display order swapped and
accepts only consistent structured output; [`scripts/auto_visual_judge.py`](scripts/auto_visual_judge.py)
also scores known original/degraded calibration pairs. A focus family becomes `ready`
only after five real tasks, five accepted three-candidate records, ten swapped pairwise
judgments, order consistency/degradation detection ≥0.90, challenger win rate ≥0.60,
scientific/L0/L1 pass, and `auto_ready=true`. The loop hard-stops at three candidates,
one repair, and two judge rounds; an uncertain result keeps the current champion. L2/L3
and coverage × quality × diversity remain diagnostics. Do not create placeholder tasks
or synthetic preference evidence.

Run the current real-paper sprint with:

```powershell
$env:PYTHONPATH = "E:\CODE\publication-figure-design\src;E:\CODE\publication-figure-design\scripts"
& "D:\Anaconda\envs\piepaper\python.exe" scripts/run_visual_sprint.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/champion_board.py --enforce --summary
```

The checked-in task manifest is
[`assets/reference-benchmarks/real_generation_tasks.json`](assets/reference-benchmarks/real_generation_tasks.json).
The run writes 75 candidate PNGs, swapped-judge records, calibration evidence, and
family contact sheets under `tmp/visual_sprint/` (kept out of Git). These candidates
are marked `source_render_variant`: the real paper render remains the semantic source,
so the run measures visual preference and calibration but does not claim a production
champion until a longitudinal challenger beats an existing champion.

The current 25-task output is frozen as `visual-baseline-v1`. To compare a later real
render against it:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/visual_regression.py `
  --current-report tmp/visual_sprint/sprint_report.json `
  --output tmp/visual_sprint/visual-regression.json
```

The report contains only unchanged/win/loss/uncertain counts, family win rates,
reason-code deltas, and hard-QA regressions. Changed renders require forward and
reverse blind-judge payloads; uncertain review blocks promotion. The baseline is a
regression checkpoint, not a Champion Board entry.

Do not overwrite a frozen baseline during ordinary development. Create a new
checkpoint only after the regression report satisfies the promotion rule, for example:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/freeze_visual_baseline.py `
  --report tmp/visual_sprint/sprint_report.json `
  --output assets/reference-benchmarks/visual-baseline-v2.json
```

The freezer derives the image directory and baseline id from the output name and
refuses to replace an existing checkpoint unless `--replace` is explicitly supplied.

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_skill_contract.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_references.py --require-previews
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_reference_dna.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_source_reconstruction_library.py
```

## Layout

```text
SKILL.md                         agent-facing entrypoint
manifest.yaml                    routes and validation commands
src/publication_figure_design/   current production runtime
scripts/                         CLI wrappers, maintenance, and gates
references/                      workflow and visual-grammar contracts
assets/figures/                  maintained figure-family scripts and previews
assets/visual-references/        reference corpus and per-image artifacts
assets/anti-pattern-atlas/       bad → diagnosis → corrected examples
profiles/journals/               journal/venue constraints
profiles/style-capsules/         reusable visual-grammar packages
profiles/domains/                field-specific semantic contracts
indexes/                         deterministic retrieval indexes
rules/                           machine-readable scientific and house rules
evals/                           activation, output eval, benchmark, and regression data
sources/registry.yaml            external evidence provenance
```

## Contributing

Read [`AGENTS.md`](AGENTS.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md). Keep one
current production path, do not revive deleted legacy runners, and do not add numbered
`v1`/`v2`/`final2` copies. New visual material needs provenance, a reproducible
companion, a preview, and the relevant reference/reconstruction checks.

## License

Distributed under the [Apache License 2.0](LICENSE). Third-party material remains
subject to its own recorded provenance and reuse scope.
