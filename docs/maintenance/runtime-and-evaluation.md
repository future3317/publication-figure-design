# Runtime and Evaluation Maintenance

This document is for repository maintainers. Ordinary figure tasks use the compact
`SKILL.md` router and persisted `RoutePlan`; they do not need benchmark policy or CI
thresholds in their working context.

## Runtime contract

`manifest.yaml` is the only source for workflow stage lists and conditional insertions.
The `WorkflowSession` persists its plan, cursor, and applied conditions so a resumed
task follows the same route, including repeated render/QA stages after a failed gate.
`RoutePlan` selects the base workflow from `TaskSpec.mode`. A supplied reference adds
retrieval, inspection, and comparison to create/revise. Failed create/revise QA adds one
critique, repair, render, QA cycle; review/export QA failures report and block without
forcing a render. Critique pauses for a `DesignPatch`, and `pfd run --resume
<session.json>` continues after the agent supplies that patch.
Sessions saved before `RoutePlan` existed are resumed once with their original stage
order, then persist that plan on the next save.

The runtime compiles selected global, house, family, route, and required journal rules
into `policy_packet` in session telemetry. The packet contains hard-rule identifiers,
concise house and family statements, required journal constraints, and current QA
feedback. Validators enforce hard constraints and surface concrete failures for the
repair step. Agent-facing instructions do not enumerate source YAML files.

Production generation defaults to one candidate. `generation_mode: evaluation` is the
only mode that emits the three structure-first, style-first, and balanced candidates
used by evaluation workflows. QA repair is limited to one inserted cycle.

## Reference and evaluation policy

New reference assets advance through `raw → analyzed → reviewed → benchmarked →
production`. Reference-local `code.py` is not executed during intake; explicit audits
use `scripts/reference_code_sandbox.py`.

The CI/release gate is `scripts/ci_gate.py`. It runs package and script tests,
reference validation/reconstruction/fidelity, DNA/index checks, benchmark/holdout,
adversarial retrieval, scale evaluation, generation regression, champion floors,
quarantine, adapters, and the orchestrator lifecycle canary.

The source-image preparation set currently covers five focus families:
`statistical_discovery`, `mechanism_architecture`, `matrix_array`,
`multi_axis_comparison`, and `image_quantitative_composite`. `run_visual_sprint.py`
only prepares deterministic source-render variants, source hashes, and L0/contact-sheet
evidence. It does not call a judge, create preference records, claim L1, or update the
Champion Board. Those variants are not generation tasks or champion evidence.

A family is ready only when real skill-generated tasks and swapped-order judge
responses satisfy the criteria in `assets/reference-benchmarks/champion_board.json`.
The release gate validates the frozen baseline contract; it cannot perform a Codex/Luna
visual judgment. `visual_regression.py` accepts only real skill renders with matching
source hashes and L0/L1 evidence. Source input changes are reported as an invalid
comparison, not as a visual win or loss.

The source-render checkpoint is `assets/reference-benchmarks/visual-baseline-v1.json`.
Its 2026-09-23 source-identity correction realigned two changed inputs and is not a
quality promotion. Future source drift must be handled as task-data correction before
longitudinal comparison. Changed skill renders require forward and reverse blind
comparisons; uncertain results block promotion.

Run the project checks with the dedicated environment:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_skill_contract.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_rule_contract.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_journal_profiles.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_references.py --require-previews
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_reference_dna.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/ci_gate.py
```

Use `scripts/run_visual_sprint.py` only to prepare source-image variants for inspection.
Use `scripts/visual_regression.py` only with actual skill-generated output. Benchmark
numbers, generation tasks, judge records, and champion promotion policy remain under
`assets/reference-benchmarks/` and `evals/`.
