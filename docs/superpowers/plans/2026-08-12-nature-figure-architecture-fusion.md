# Nature-Figure Architecture Fusion Implementation Plan

Date: 2026-08-12

## Goal

Refactor `academic-figure-skill` into a short evidence-first router, unify reference/template adaptation decisions, and add a lightweight deterministic contract checker plus focused safety utilities.

## Task 1: Define failing architecture tests

Files:

- Add `scripts/test_skill_contract.py`
- Extend `scripts/test_reference_fidelity.py`

Tests:

- Assert root `manifest.yaml` exists and every routed resource exists.
- Assert `SKILL.md` is below 300 lines and reference inspection precedes asset selection.
- Assert the four unified adaptation levels and five structural dimensions exist.
- Assert backend policy names explicit/workflow/saved/default precedence and mixed-mode assembler exception.
- Assert privacy, legend, PDF audit, safety helper, and `agents/openai.yaml` routes exist.
- Assert reference contracts expose a normalized adaptation level consistent with the existing decision.

Run the focused tests and record expected failures before implementation.

## Task 2: Implement the short router and declarative manifest

Files:

- Replace `SKILL.md`
- Add `manifest.yaml`
- Add `references/workflow-create.md`
- Add `references/asset-adaptation.md`
- Add `references/backend-selection.md`
- Add `references/delivery-contract.md`

Implementation:

- Preserve the five request modes and current hard reference gate.
- Put observable reference decisions before any legacy asset scan.
- Route detailed creation, asset mapping, backend, and delivery behavior out of the hub.
- Preserve existing APIs and assets.

Run architecture tests until this task is green.

## Task 3: Normalize adaptation evidence

Files:

- Update `references/reference-driven-reconstruction.md`
- Update `scripts/check_reference_fidelity.py`
- Update `scripts/test_reference_fidelity.py`

Implementation:

- Add `adaptation_level` to the contract.
- Enforce allowed mappings between `reuse/restructure/rewrite` and the four-level ladder.
- Keep the existing no-cosmetic-reconstruction gate.

Run reference-fidelity tests.

## Task 4: Add backend preference and safety utilities

Files:

- Add `scripts/backend_preference.py`
- Add `scripts/figure_safety.py`
- Add `scripts/audit_pdf_text.py`
- Add `scripts/test_figure_safety.py`

Implementation:

- Persist only an explicit Python/R choice in a small JSON config.
- Allow a test-only config-path environment override.
- Add strictly monotone interpolation and uncertainty-aware label placement.
- Audit supported PDF content streams for actual `Tf` font sizes.

Run the new utility tests and CLI smoke checks.

## Task 5: Add legend/privacy contracts and UI metadata

Files:

- Add `references/figure-legend-contract.md`
- Add `references/privacy-provenance.md`
- Add `agents/openai.yaml`

Implementation:

- Keep exact provenance in internal artifacts; hide private paths in ordinary user-facing summaries.
- Define compact figure-title, panel, statistics, uncertainty, and source-data legend requirements.
- Generate valid UI-facing metadata for the skill.

Run architecture tests and skill quick validation.

## Task 6: Add the lightweight self-check

Files:

- Add `scripts/check_skill_contract.py`
- Extend `scripts/test_skill_contract.py`

Implementation:

- Validate frontmatter, line budget, manifest structure, route target existence, gate ordering, adaptation vocabulary, metadata, and absence of `figures4papers` dependencies.
- Emit text and JSON reports; return non-zero on failures.

Run positive tests plus temporary-copy mutation tests that prove each failure is detected.

## Task 7: Regression and validation

Run:

```powershell
python -m unittest discover -s scripts -p "test_*.py" -v
python scripts/check_skill_contract.py
python scripts/check_references.py --json
python scripts/qa_coverage.py --json
python scripts/e2e_smoke_test.py
python C:\Users\LRH\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
git diff --check
git status --short
```

Resolve failures without weakening tests. Review the final diff for licence boundaries and accidental changes to user assets.
