# Project instructions

## Scope

This repository is the current implementation of the `publication-figure-design`
Scientific Figure Design Compiler. `SKILL.md` is the thin agent-facing entry point;
the production runtime lives in `src/publication_figure_design/`.

## Figure workflow

For ordinary figure work, follow `SKILL.md` directly: inspect the task and relevant
visual evidence, edit or build the figure source, render it, inspect the actual output,
and repair visible problems. Do not require a TaskSpec, PolicyPacket, RoutePlan, or
session file for routine drawing. The `pfd run` CLI is an optional session/QA helper; it
does not render figures and its stage output never substitutes for the actual figure.

The scientific contract is authoritative. References provide visual grammar only and
must not change data meaning, statistical transforms, uncertainty semantics, labels, or
variable roles. Inspect selected pixels and retrieve structure, style, palette,
component, and annotation roles independently when useful. Compile the evidence into
`ReferenceDNA → StyleCapsule + JournalProfile → DesignPacket`.

The runtime can compile applicable rules into a `PolicyPacket` for callers that use the
optional session runner. For ordinary work, apply the concise global requirements in
`SKILL.md`; load a specialized reference only when the task needs it. Production drawing
does not need evaluation candidates.

## Current sources of truth

- Contracts and runtime: `src/publication_figure_design/`
- Agent workflow: `SKILL.md`; optional session-runner graph: `manifest.yaml`
- Rule hierarchy and provenance: `rules/`, `sources/registry.yaml`,
  `scripts/check_rule_contract.py`
- Runtime policy: `manifest.yaml` owns workflow stages and rule selection for the
  optional `pfd run` session runner. `docs/maintenance/runtime-and-evaluation.md` owns
  maintainer-only benchmark and release procedures.
- Reference intelligence: `reference_dna.json`, `indexes/hybrid.json`
- Style: `profiles/style-capsules/`, `profiles/journals/`
- Reference lifecycle: `raw → analyzed → reviewed → benchmarked → production`
- Evaluation: `evals/`, `assets/reference-benchmarks/`, `scripts/ci_gate.py`

Ordinary figure-generation tasks must not invoke the session runner by default or inherit
benchmark thresholds, sprint families, visual-judge policy, or baseline-promotion
details from maintainer documentation.

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
