# Project instructions

## Scope

This repository is the current implementation of the `publication-figure-design`
Scientific Figure Design Compiler. `SKILL.md` is the thin agent-facing entry point;
the production runtime lives in `src/publication_figure_design/`.

## Required workflow

For create, revise, review, export, optimization, or reference-intake work, use the
orchestrated lifecycle:

`Route → Intake → Reference Retrieval → Reference Inspection → Design Spec → Binding → Render → Compare → Critique → Repair → QA → Export`

The scientific contract is authoritative. References provide visual grammar only and
must never change data meaning, statistical transforms, uncertainty semantics, labels,
or variable roles.

Reference-led work must retrieve roles independently (`structure`, `style`, `palette`,
`component`, and `annotation` when needed), inspect the selected pixels, and compile
them into `ReferenceDNA → StyleCapsule + JournalProfile → DesignPacket`. Publication
mode produces structure-first, style-first, and balanced candidates before final
rendering. Critique returns deterministic `DesignPatch` operations, and renderers emit
`RenderTrace` for scientific QA.

## Current sources of truth

- Contracts and runtime: `src/publication_figure_design/`
- Agent routing and gates: `SKILL.md`, `manifest.yaml`
- Rule hierarchy and provenance: `rules/`, `sources/registry.yaml`,
  `scripts/check_rule_contract.py`
- Reading contract: `always_load` and route-level `required_load` are mandatory; ordinary
  `load` entries are supplemental and must not be treated as a substitute for required
  material.
- Reference intelligence: `reference_dna.json`, `indexes/hybrid.json`
- Style: `profiles/style-capsules/`, `profiles/journals/`
- Reference lifecycle: `raw → analyzed → reviewed → benchmarked → production`
- Evaluation: `evals/`, `assets/reference-benchmarks/`, `scripts/ci_gate.py`

Rules are categorized as G0 scientific invariants, G1 accessibility/legibility, J
journal/stage requirements, F figure-family constraints, H house defaults, and B
backend details. Precedence is `G0 > G1 > J > explicit user requirement > F > H > B`;
conflicts between non-overridable rules block. Benchmark/champion state is evaluation
policy, not a scientific rule.

Do not revive deleted `eval_runner.py`, `e2e_runner.py`, `run_ab_tests.py`, or
metadata-proxy ranking. Do not create ordinary `v1`, `v2`, `final2`, or parallel
production implementations. Extend the current contracts and remove replaced callers
when an interface changes.

## Runtime and dependencies

Run every repository Python command with the project environment's explicit interpreter:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" <script-or-module>
```

Never silently fall back to Conda `base`, system Python, or an unrelated environment.
Install optional extras into `piepaper`; keep Torch/model downloads out of core figure
work unless the requested route needs them.

Do not execute reference-local `code.py` during intake. Use static AST analysis; an
explicit private audit may use `scripts/reference_code_sandbox.py`.

## Verification

After implementation and old-path cleanup, run the relevant narrow checks and then the
full release gate:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_skill_contract.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_reference_dna.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/reference_library.py validate
& "D:\Anaconda\envs\piepaper\python.exe" scripts/ci_gate.py
```

`ci_gate.py` is the merge/release gate. It covers unit/package tests, reference
validation, DNA and fidelity, benchmark/holdout/adversarial/scale evaluation,
generation regression, champion floors, quarantine, activation, adapters, and the
orchestrator lifecycle canary. Use `git diff --check` before handoff. Preserve
unrelated user changes and do not delete untracked data, experiment outputs, or
private reference material merely because it is under `tmp/`, `runs/`, or another
ignored path.
