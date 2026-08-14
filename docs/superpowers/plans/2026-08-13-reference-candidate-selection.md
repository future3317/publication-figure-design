# Reference Candidate Selection Implementation Plan

**Goal:** Replace global-top-three behavior with strict, explainable, diversified task-specific candidate recommendation.

**Architecture:** Add `ReferenceLibrary.recommend_candidates()` and a CLI `recommend` route; retain `query()` for maintenance. Require the recommendation report in the visual-optimization contract and document the pixel-inspection sequence.

**Tech Stack:** Python standard library, unittest, existing side-car metadata.

### Task 1: Recommendation behavior

- [ ] Write failing tests for required figure type, hard compatibility filters, compatibility-first scoring, diversity, exclusions, and shortage reporting.
- [ ] Implement deterministic recommendation and report generation.
- [ ] Add CLI coverage.

### Task 2: Workflow enforcement

- [ ] Require a recommendation report in visual-optimization QA.
- [ ] Update SKILL.md and reference workflow to forbid generic query for optimization candidate selection.
- [ ] Require pixel inspection and recorded candidate-specific selection reasons.

### Task 3: Verification

- [ ] Run focused tests and real-library recommendation scenarios.
- [ ] Run all unit, contract, integrity, QA-coverage, and end-to-end checks.
- [ ] Run `git diff --check`.
