# Reference-Driven Reconstruction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make concrete reference images control scientific figure reconstruction and reject cosmetic-only adaptation with a lightweight checker.

**Architecture:** Route concrete-reference requests into a hard-gated `reference-driven` submode. Store the detailed reconstruction contract in one reference document, validate its process evidence with one dependency-free checker, and extend the existing e2e and integrity suites rather than adding a new registry or manager.

**Tech Stack:** Markdown skill instructions, Python 3 standard library, `unittest`, existing e2e and reference-integrity scripts.

## Global Constraints

- Scientific meaning, data integrity, and non-misleading encoding outrank visual fidelity.
- A concrete user-selected reference outranks reusable production code and skill defaults.
- `COPY-FIRST` is suspended until reference compatibility is classified.
- `reuse` requires matching panel topology, mark geometry, layer topology, data encoding, and annotation/legend model.
- Cosmetic-only changes cannot satisfy `restructure` or `rewrite`.
- Add no external dependency, image embedding system, manager, registry, or production-asset rewrite.

---

### Task 1: Capture the Existing Failure and Checker Contract

**Files:**
- Create: `tmp/reference-driven-baseline.md`
- Create: `scripts/test_reference_fidelity.py`
- Test: `scripts/test_reference_fidelity.py`

**Interfaces:**
- Consumes: the existing `SKILL.md` behavior and the JSON contract schema in the design.
- Produces: expected CLI and function behavior for `check_reference_fidelity.py`.

- [ ] **Step 1: Record the RED behavior**

Write a baseline record quoting the current rules that make references optional and preserve production layout. Include the expected failure: an incompatible old skeleton can pass current QA after cosmetic changes.

- [ ] **Step 2: Write failing checker tests**

Create tests that import `validate_reference_fidelity` and assert:

```python
def test_rewrite_rejects_cosmetic_only_changes(self):
    report = validate_reference_fidelity(
        script_text=SCRIPT_MARKER,
        contract=contract(decision="rewrite", structural_changes=[]),
        comparison_path=self.comparison,
    )
    self.assertFalse(report["ready"])
    self.assertIn("cosmetic", " ".join(report["errors"]).lower())
```

Also test a valid rewrite, a reuse without compatibility evidence, unresolved must-match items, and a missing comparison image.

- [ ] **Step 3: Run tests to verify RED**

Run: `python scripts/test_reference_fidelity.py`

Expected: FAIL because `check_reference_fidelity` does not exist.

- [ ] **Step 4: Commit RED evidence**

```powershell
git add tmp/reference-driven-baseline.md scripts/test_reference_fidelity.py
git commit -m "test: define reference fidelity contract"
```

---

### Task 2: Implement the Lightweight Fidelity Checker

**Files:**
- Create: `scripts/check_reference_fidelity.py`
- Modify: `scripts/test_reference_fidelity.py`

**Interfaces:**
- Consumes: `script_text: str`, `contract: dict`, and `comparison_path: Path | None`.
- Produces: `validate_reference_fidelity(...) -> dict` with `ready`, `errors`, `warnings`, and `checks`; CLI exit code `0` for READY and `1` otherwise.

- [ ] **Step 1: Implement required-field and decision validation**

Define:

```python
REQUIRED_FIELDS = (
    "reference_source", "scientific_invariants", "canvas_layout",
    "mark_geometry", "layer_topology", "data_encoding", "palette_roles",
    "typography", "legend_annotation", "spacing_hierarchy", "must_match",
    "may_adapt", "implementation_decision", "decision_evidence",
    "structural_changes", "fidelity_review",
)
```

Require `# AFS-REFERENCE-DRIVEN: true` in the script and validate decision-specific evidence.

- [ ] **Step 2: Implement fidelity-review and comparison validation**

Every `must_match` item must have a review entry with `status: pass` or `status: justified_deviation`; deviations require a non-empty reason. When a comparison path is supplied, require an existing non-empty file.

- [ ] **Step 3: Implement CLI**

Support:

```text
python scripts/check_reference_fidelity.py generated.py --contract contract.json --comparison comparison.png --json report.json
```

Print a compact READY/FIX report and optionally save JSON.

- [ ] **Step 4: Run focused tests to verify GREEN**

Run: `python scripts/test_reference_fidelity.py`

Expected: all tests pass.

- [ ] **Step 5: Commit checker**

```powershell
git add scripts/check_reference_fidelity.py scripts/test_reference_fidelity.py
git commit -m "feat: add reference fidelity checker"
```

---

### Task 3: Rewrite the Skill Routing and Reconstruction Contract

**Files:**
- Modify: `SKILL.md`
- Create: `references/reference-driven-reconstruction.md`
- Modify: `references/visual-reference-library.md`

**Interfaces:**
- Consumes: concrete reference image/path/selected library reference.
- Produces: mode routing, required contract comment marker, and `reuse|restructure|rewrite` decision.

- [ ] **Step 1: Add a failing structural e2e scenario**

Add `S6_reference_reconstruction` to `scripts/e2e_runner.py`. Require the reference marker, reconstruction decision, contract path, structural-change evidence, comparison output, and checker call. Reject scripts that declare `rewrite` or `restructure` but contain only cosmetic-change declarations.

- [ ] **Step 2: Verify e2e RED**

Pipe a cosmetic-only legacy adaptation into the S6 scenario.

Run: `python scripts/e2e_runner.py --scenario S6_reference_reconstruction --stdin`

Expected: threshold not met.

- [ ] **Step 3: Add hard routing and precedence to `SKILL.md`**

Insert `reference-driven` dispatch before the normal create pipeline. State that production asset selection happens only after the reconstruction contract and compatibility classification. Replace conflicting Step 4.5 optional-reference language for concrete-reference requests.

- [ ] **Step 4: Add the focused reconstruction reference**

Write `references/reference-driven-reconstruction.md` with the contract schema, decision matrix, required script comment block, render/compare loop, rationalization table, and red flags. Keep detailed mechanics out of `SKILL.md`.

- [ ] **Step 5: Align visual-reference documentation**

Update `references/visual-reference-library.md` to distinguish optional style retrieval from mandatory concrete-reference reconstruction and apply the new precedence.

- [ ] **Step 6: Run S6 with a compliant fixture**

Run a fixture containing the marker, contract, structural rewrite evidence, comparison path, and checker invocation.

Expected: S6 meets threshold.

- [ ] **Step 7: Commit workflow changes**

```powershell
git add SKILL.md references/reference-driven-reconstruction.md references/visual-reference-library.md scripts/e2e_runner.py
git commit -m "feat: enforce reference-driven reconstruction"
```

---

### Task 4: Add Reference Fidelity QA and Integrity Coverage

**Files:**
- Modify: `references/checklist.md`
- Modify: `scripts/check_references.py`
- Modify: `scripts/test_workflow_integration.py`

**Interfaces:**
- Consumes: reconstruction contract, comparison image, and checker report.
- Produces: RF-1 through RF-10 QA gate and reference-file health coverage.

- [ ] **Step 1: Write failing integration assertions**

Assert that `SKILL.md` routes concrete references before `COPY-FIRST`, mentions the checker, and links the new reference; assert the checklist contains RF-1 through RF-10.

- [ ] **Step 2: Run integration tests to verify RED**

Run: `python scripts/test_workflow_integration.py`

Expected: new assertions fail before QA documentation is complete.

- [ ] **Step 3: Add RF-1 through RF-10**

Append the reference-specific pass after normal visual verification. Set the gate to FIX when a must-match feature is unresolved or the comparison was not inspected.

- [ ] **Step 4: Register reference health checks**

Add `reference-driven-reconstruction.md` to the required reference list in `check_references.py`.

- [ ] **Step 5: Run integration and integrity tests to verify GREEN**

Run:

```text
python scripts/test_workflow_integration.py
python scripts/check_references.py
```

Expected: pass and HEALTHY.

- [ ] **Step 6: Commit QA changes**

```powershell
git add references/checklist.md scripts/check_references.py scripts/test_workflow_integration.py
git commit -m "test: gate reference reconstruction fidelity"
```

---

### Task 5: Forward-Test and Run Full Regression

**Files:**
- Modify as required by observed failures only: `SKILL.md`, `references/reference-driven-reconstruction.md`, `scripts/check_reference_fidelity.py`, tests.
- Update: `tmp/reference-driven-baseline.md`

**Interfaces:**
- Consumes: the same pressure scenario used for baseline.
- Produces: recorded before/after behavior and a clean regression run.

- [ ] **Step 1: Repeat the pressure scenario with the revised skill**

Ask for a figure that must resemble a concrete reference while supplying an incompatible old plotting script and time pressure. Verify the response chooses `restructure` or `rewrite`, creates a contract, and requires comparison QA.

- [ ] **Step 2: Close observed loopholes**

If the agent rationalizes cosmetic adaptation, add only the counter needed to `references/reference-driven-reconstruction.md`, then repeat the scenario.

- [ ] **Step 3: Run focused and full checks**

Run:

```text
python scripts/test_reference_fidelity.py
python scripts/test_workflow_integration.py
python scripts/test_phase5_workflow.py
python scripts/test_reference_library.py
python scripts/test_production_asset_manager.py
python scripts/test_palette_manager.py
python scripts/check_references.py
python scripts/regression_benchmark.py
python scripts/qa_coverage.py
```

Expected: all available tests pass; environment-dependent R cases may report their existing documented skip/warn.

- [ ] **Step 4: Validate the skill package**

Run:

```text
python C:/Users/LRH/.codex/skills/.system/skill-creator/scripts/quick_validate.py C:/Users/LRH/.agents/skills/academic-figure-skill
```

Expected: valid skill.

- [ ] **Step 5: Review the diff and commit final refinements**

```powershell
git diff --check HEAD~4..HEAD
git status --short
git add SKILL.md references scripts tmp/reference-driven-baseline.md
git commit -m "refactor: close reference reconstruction loopholes"
```
