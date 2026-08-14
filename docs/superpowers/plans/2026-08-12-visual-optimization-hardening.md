# Visual Optimization Hardening Implementation Plan

> **For agentic workers:** Execute inline with test-driven development; no subagent is required.

**Goal:** Close the paths that let cosmetic edits and unreviewed synthetic examples pass as publication-quality visual optimization.

**Architecture:** Add executable source QA, canonical reference taxonomy and eligibility filtering, an evidence-backed rendered optimization checker, and mandatory workflow documentation. Keep side-car metadata as the reference-library source of truth.

**Tech Stack:** Python standard library, Pillow, unittest, Markdown/YAML contracts.

## Global Constraints

- Existing user figure files are diagnostic fixtures only and are not modified.
- Automated generation never grants aesthetic approval.
- A READY optimization requires actual render evidence and structural changes.

### Task 1: Executable source QA

**Files:** Modify `scripts/qa_validator.py`; create `scripts/test_qa_validator_cli.py`.

- [ ] Add tests for structured output, JSON output, and nonzero FAIL exit.
- [ ] Implement `validate_source`, reporting, argument parsing, and `main`.
- [ ] Run the focused tests.

### Task 2: Canonical retrieval and quarantine

**Files:** Modify `scripts/reference_library.py`, `scripts/test_reference_library.py`, `scripts/source_reconstruction_library.py`, and `scripts/test_source_reconstruction_library.py`.

- [ ] Add failing alias and default-eligibility tests.
- [ ] Normalize figure types on ingest and query; exclude unreviewed entries unless explicitly requested.
- [ ] Ensure generated reconstructions are pending and unrated.
- [ ] Migrate installed source reconstructions and rebuild the registry.

### Task 3: Rendered optimization evidence

**Files:** Create `scripts/check_visual_optimization.py` and `scripts/test_visual_optimization.py`; modify `scripts/check_reference_fidelity.py` and its tests.

- [ ] Add tests for real images, authentic comparison composition, structural change evidence, and final-size review fields.
- [ ] Implement lightweight image metrics and optimization-contract validation.
- [ ] Make reference fidelity reject arbitrary non-image comparison files and unauthentic comparisons.

### Task 4: Workflow hardening

**Files:** Modify `SKILL.md`, `manifest.yaml`, `references/workflow-create.md`, `references/reference-driven-reconstruction.md`, `references/visual-reference-library.md`, `references/source-reconstruction-library.md`, and `references/checklist.md`.

- [ ] Define the mandatory visual-optimization route.
- [ ] Require candidate pixel inspection, structural diagnosis, before/after evidence, and rendered gate execution.
- [ ] Document review-state integrity and prohibit cosmetic-only delivery claims.

### Task 5: Verification

- [ ] Run focused red/green tests.
- [ ] Run all unit tests and skill contract checks.
- [ ] Run reference and source-library integrity checks.
- [ ] Run end-to-end smoke checks and `git diff --check`.
