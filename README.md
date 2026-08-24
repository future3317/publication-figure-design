# Publication Figure Design

Reference-first scientific figure design for publication workflows. This repository
contains the current implementation of the `publication-figure-design` Codex Skill:
an orchestrated compiler that turns a scientific contract and visual evidence into a
reproducible, QA-gated figure package.

The project is not a template gallery. A reference supplies visual grammar only; it
never changes the data meaning, statistical transform, uncertainty semantics, labels,
or variable roles of the target figure.

## What is here

- A thin agent entrypoint in [`SKILL.md`](SKILL.md) and the routing manifest in
  [`manifest.yaml`](manifest.yaml).
- The production runtime in
  [`src/publication_figure_design/`](src/publication_figure_design/): contracts,
  reference intelligence, style compilation, layout, renderers, orchestration, and
  layered QA.
- Reference assets under [`assets/`](assets/), with source-specific analysis,
  `ReferenceDNA`, reproduction material, previews, provenance, and lifecycle state.
- Journal profiles and reusable style capsules in [`profiles/`](profiles/), plus
  deterministic hybrid indexes in [`indexes/`](indexes/).
- Executable evaluation and release gates in [`scripts/`](scripts/) and [`evals/`](evals/).

## Runtime lifecycle

Every create, revise, review, export, optimization, and reference-intake task follows
the same persisted route:

```text
Route → Intake → Reference Retrieval → Reference Inspection
      → Design Spec → Binding → Render → Compare → Critique
      → Repair → QA → Export
```

The runtime records the selected reference ids, concrete index version, renderer and
style versions, iteration history, QA artifacts, and output manifest. Resuming a
session reuses its recorded selection; it does not silently re-rank references.

Reference retrieval is role-separated (`structure`, `style`, `palette`, `component`,
and `annotation`). The selected pixels are inspected before implementation material is
chosen and compiled into `ReferenceDNA → StyleCapsule + JournalProfile → DesignPacket`.
Publication mode renders structure-first, style-first, and balanced candidates before
the final repair and export decision.

### 阅读材料契约

`manifest.yaml` 将材料分成三层：`always_load` 是所有任务必读，路由下的
`required_load` 是进入该路由时必读，普通 `load` 是按任务需要查阅的补充材料。
路由的强制材料没有读完或文件缺失时，不得进入 Render、QA 或 Export；
[`scripts/check_skill_contract.py`](scripts/check_skill_contract.py) 会检查这份合同。

## Quick start

Use the repository's dedicated `piepaper` environment. On the maintainer workstation,
call its interpreter directly:

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

Do not use Conda `base`, a bare system `python`, or an unrelated environment for
repository commands. Optional renderer and reference-analysis dependencies are listed
in [`pyproject.toml`](pyproject.toml); install them into `piepaper` only for the route
that needs them.

## Reference library contract

An image added to the library advances through:

```text
raw → analyzed → reviewed → benchmarked → production
```

Each production reference is expected to have a machine-readable metadata record,
source-appropriate analysis, a reproducible reconstruction or reproduction artifact,
a preview, provenance, and passing retrieval/generation canaries. Reference-local
`code.py` is not executed during intake; an explicitly requested private audit uses
the constrained [`scripts/reference_code_sandbox.py`](scripts/reference_code_sandbox.py).

The reference index is transparent and versioned. `current` is only an alias; the
underlying index record retains the corpus, schema, model, and build identity needed
to reproduce a past selection.

## Quality gates

The release gate is [`scripts/ci_gate.py`](scripts/ci_gate.py). It runs unit and
package tests, reference validation and reconstruction/fidelity checks, DNA/index
checks, benchmark/holdout/adversarial/scale evaluation, generation regression,
champion floors, quarantine, adapter canaries, and the orchestrator lifecycle canary.

The figure QA layers remain separate:

- **L0** technical/export contract;
- **L1** scientific correctness and provenance;
- **L2** structural visual alignment;
- **L3** perceptual quality, typography, contrast, density, and finish.

Reference-led renderers must explicitly consume `TypographySpec`, `PaletteSpec`,
`LayoutSpec`, and `ComponentSpec`. A high visual similarity score cannot override a
scientific or export failure.

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

Do not overwrite a frozen baseline during ordinary development. A new baseline is
created only after the regression report satisfies the promotion rule, for example:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/freeze_visual_baseline.py `
  --report tmp/visual_sprint/sprint_report.json `
  --output assets/reference-benchmarks/visual-baseline-v2.json
```

The freezer derives the image directory and baseline id from the output name and
refuses to replace an existing checkpoint unless `--replace` is explicitly supplied.

For a focused check:

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
profiles/                        journal profiles and style capsules
indexes/                         deterministic retrieval indexes
evals/                           activation, benchmark, and regression data
```

## Contributing

Read [`AGENTS.md`](AGENTS.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md) first. Keep one
current production path, do not revive deleted legacy runners, and do not add numbered
`v1`/`v2`/`final2` copies. New visual material needs provenance, a reproducible
companion, a preview, and the relevant reference/reconstruction checks.

## License

The project is distributed under the [Apache License 2.0](LICENSE). Third-party
material remains subject to its own recorded provenance and reuse scope.
