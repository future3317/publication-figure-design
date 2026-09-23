# Publication Figure Design

A reference-first scientific figure design skill and compiler for research fields and
publication venues. It connects the scientific task, visual evidence, layout/style
specifications, rendered output, and layered QA in a resumable workflow.

References provide visual grammar only. They never change source data, statistical
transforms, uncertainty semantics, variable roles, or scientific conclusions.

## Project map

- [`SKILL.md`](SKILL.md): compact agent entrypoint.
- [`manifest.yaml`](manifest.yaml): single source for workflow stages, conditional
  insertions, rule sources, and adapter runtime bundle.
- [`src/publication_figure_design/`](src/publication_figure_design/): contracts,
  reference intelligence, style compilation, layout, renderers, orchestration, and QA.
- [`rules/`](rules/) and [`sources/registry.yaml`](sources/registry.yaml): machine rules,
  authority hierarchy, and provenance.
- [`profiles/`](profiles/) and [`indexes/`](indexes/): journal/domain profiles,
  StyleCapsules, and retrieval indexes.
- [`assets/`](assets/): reference corpus, ReferenceDNA, reproduction material, and the
  anti-pattern atlas.
- [`evals/`](evals/) and [`scripts/`](scripts/): separate benchmark, maintenance, and
  release tooling.

## Workflow

Every `WorkflowSession` persists its `RoutePlan`, stage cursor, reference selections,
compiled policy, QA results, and export information. Create/revise run only the stages
needed for the task. Review and export use shorter paths. References add retrieval,
pixel inspection, and comparison only when present. Failed create/revise QA inserts
at most one critique → repair → render → QA cycle. Critique pauses with concrete
failures until the agent supplies a `DesignPatch` and resumes with `--resume`;
review/export failures report and block without forcing a render.

```text
TaskSpec → RoutePlan → PolicyPacket → stage handlers → QA feedback → Export
```

`manifest.yaml` is the sole source for the execution graph. The runtime compiles the
applicable global, house, family, route, and journal constraints into a compact
`PolicyPacket`. Validators enforce hard constraints and provide concrete failures to
the repair step; agents do not load the full rule YAML corpus for every task.

References are selected by roles such as `structure`, `style`, `palette`, `component`,
and `annotation`. After pixel inspection, evidence is compiled into
`ReferenceDNA → StyleCapsule + JournalProfile → DesignPacket`. Production defaults to
one candidate; evaluation may explicitly request structure-first, style-first, and
balanced candidates.

The house visual language uses soft segmentation, short title hierarchy, structured
whitespace, low-saturation semantic colors, and restrained legends and annotations.
Accessibility contrast and scientific meaning remain authoritative.

## TeX backend

TeX/TikZ/PGFPlots is a first-class backend. When selected, read
[`references/tex-rendering.md`](references/tex-rendering.md), declare the engine and
package versions, and include compiler logs, font embedding, overfull boxes, page
dimensions, and a target-size PNG in QA. Missing TeX support blocks the backend instead
of silently switching renderers.

## Quick start

Use the dedicated `piepaper` environment:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" -m pip install -e .
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli run <task-spec.json>
```

Do not use Conda `base`, bare system Python, or an unrelated environment. Install
optional dependencies into `piepaper` only when the selected route needs them.

## References and quality gates

New references advance through `raw → analyzed → reviewed → benchmarked → production`.
Production references need metadata, applicable analysis and reproduction material, a
preview, provenance, and passing canaries. Intake never executes reference-local
`code.py`.

QA separately records technical/export integrity, scientific correctness, structural
visual alignment, and perceptual quality. Visual similarity cannot override scientific
or export failures. Reference-led renderers must consume `TypographySpec`,
`PaletteSpec`, `LayoutSpec`, and `ComponentSpec`.

CI, visual sprint, holdout, blind judging, champion promotion, and baseline maintenance
are maintainer workflows documented in
[`docs/maintenance/runtime-and-evaluation.md`](docs/maintenance/runtime-and-evaluation.md).
Read [`AGENTS.md`](AGENTS.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md) before making
repository changes. Keep one current production implementation; do not restore deleted
runners or add ordinary `v1/v2/final2` copies.
