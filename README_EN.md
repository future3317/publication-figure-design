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
- [`profiles/`](profiles/) and [`indexes/`](indexes/) contain journal/style profiles and
  deterministic hybrid retrieval indexes.
- [`scripts/`](scripts/) and [`evals/`](evals/) contain maintenance commands and the
  executable evaluation/release gates.

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

After the architecture is frozen, visual improvement is measured with publication-mode
structure-first/style-first/balanced candidates and human pairwise choices. The
[`Figure Family Champion Board`](references/champion-board.md) records preferred and
rejected candidates, reason codes, family champion/challenger, QA layers, and repair
iterations. Its KPI is coverage × quality × diversity; unseeded families remain
`needs_evidence`.

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

Read [`AGENTS.md`](AGENTS.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md). Keep one
current production path, do not revive deleted legacy runners, and do not add numbered
`v1`/`v2`/`final2` copies. New visual material needs provenance, a reproducible
companion, a preview, and the relevant reference/reconstruction checks.

## License

Distributed under the [Apache License 2.0](LICENSE). Third-party material remains
subject to its own recorded provenance and reuse scope.
