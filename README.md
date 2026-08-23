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

After the architecture is frozen, visual improvement is measured with publication-mode
structure-first/style-first/balanced candidates and human pairwise choices. The
[`Figure Family Champion Board`](references/champion-board.md) records the preferred and
rejected candidates, reason codes, family champion/challenger, QA layers, and repair
iterations. Its KPI is coverage × quality × diversity; unseeded families remain
`needs_evidence`.

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
