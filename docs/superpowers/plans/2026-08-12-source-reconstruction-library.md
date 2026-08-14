# Source Reconstruction Library Implementation Plan

> **For agentic workers:** Execute inline with strict RED-GREEN-REFACTOR cycles; no subagent is required for this plan.

**Goal:** Build and verify a 54-item independent visual-grammar reconstruction library from the two audited source collections.

**Architecture:** One focused module discovers sources, classifies visual grammar, renders deterministic synthetic figures, archives them, and writes an audit manifest. A small wrapper validates the installed output without source checkouts.

**Tech Stack:** Python 3, pathlib, hashlib, json, Matplotlib, NumPy, Pillow, unittest.

## Global Constraints

- Never copy source pixels or source plotting code.
- Never write local absolute paths into assets or metadata.
- Keep each source SHA mapped to exactly one generated archive entry.
- Preserve all existing reference-library assets.
- Use the existing `ReferenceLibrary` as the archive boundary.

---

### Task 1: Discovery and provenance contract

**Files:**
- Create: `scripts/test_source_reconstruction_library.py`
- Create: `scripts/source_reconstruction_library.py`

- [ ] Write tests asserting 15 licensed and 39 observation-only source records, 54 unique hashes, relative paths, dimensions, and actions.
- [ ] Run the focused test and confirm failure because the module is absent.
- [ ] Implement `discover_sources(nature_root, figures_root)` and `classify_visual_family(record)`.
- [ ] Run the focused discovery tests to green.

### Task 2: Deterministic independent rendering

**Files:**
- Modify: `scripts/test_source_reconstruction_library.py`
- Modify: `scripts/source_reconstruction_library.py`

- [ ] Add tests for valid PNG output, stable rendering, output/source SHA inequality, and no source-code imports.
- [ ] Confirm the tests fail for missing rendering behavior.
- [ ] Implement the compact family renderer registry and standalone archived rendering program.
- [ ] Run focused rendering tests to green.

### Task 3: Archive and idempotent manifest

**Files:**
- Modify: `scripts/test_source_reconstruction_library.py`
- Modify: `scripts/source_reconstruction_library.py`
- Create: `scripts/check_source_reconstruction_library.py`

- [ ] Add tests for generated-archive metadata, one record per source SHA, existing-copy audit links, and a no-growth second run.
- [ ] Confirm the tests fail for missing archive behavior.
- [ ] Implement build, audit-manifest serialization, installed-library validation, and the wrapper CLI.
- [ ] Run focused tests to green.

### Task 4: Skill routing and maintenance policy

**Files:**
- Modify: `scripts/test_skill_contract.py`
- Modify: `scripts/check_skill_contract.py`
- Create: `references/source-reconstruction-library.md`
- Modify: `SKILL.md`
- Modify: `manifest.yaml`

- [ ] Replace the repository-name ban test with a behavior test that permits audit mentions but prohibits runtime dependency/import instructions.
- [ ] Confirm the revised contract test fails.
- [ ] Add the maintenance route and concise operating reference, then update the contract checker.
- [ ] Run focused contract tests to green.

### Task 5: Build and verify all assets

**Files:**
- Create: `assets/visual-references/source-reconstruction-manifest.json`
- Create: 54 archive directories under `assets/visual-references/generated-archive/`
- Modify: `assets/registry.jsonl`

- [ ] Run the builder against the two audited checkouts.
- [ ] Run it a second time and confirm zero new archive entries.
- [ ] Run the lightweight installed-library checker and reference-library validation.
- [ ] Create and inspect a contact sheet covering all 54 outputs.
- [ ] Run all unit tests, skill contract, quick validation, reference checks, QA coverage, end-to-end smoke test, and `git diff --check`.
