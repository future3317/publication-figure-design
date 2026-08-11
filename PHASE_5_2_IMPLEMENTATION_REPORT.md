# Phase 5.2 Implementation Report: Stabilization & Regression Freeze

## Goal

Stabilize the current academic-figure-skill system, fill the last obvious gaps,
and establish a fixed regression benchmark. After this phase the skill moves
from active architecture expansion into actual use: new features, new managers,
new registries, or large reference ingestion should only happen when real
usage exposes a concrete problem.

## What changed

### 1. Completed reproduction code for the remaining WeChat references

The two WeChat screenshots that still lacked code now have standalone Python
reproduction scripts stored inside their Visual Reference asset directories:

| Reference ID | Figure Type | Location | What it reproduces |
|---|---|---|---|
| `8fbf151c1f63de42` | BarCategorical | `assets/visual-references/references/8fbf151c1f63de42/code.py` | Gradient-fill categorical bars with error bars, value labels, and a dashed trend line |
| `e088eda258e1bd3a` | MarginalDensity | `assets/visual-references/references/e088eda258e1bd3a/code.py` | 2×2 grid of scatter panels with marginal KDE, histogram, boxplot, and grouped regression lines |

Both scripts:
- Use only numpy + pandas + matplotlib + scipy
- Generate fixed synthetic demo data with deterministic seeds
- Support Chinese labels via Microsoft YaHei / SimHei fallback
- Have no local absolute paths
- Produce a `preview.png` inside the reference directory

The original WeChat images remain `usage_scope: private_reference` and
`review_status: pending`. The scripts are **not** promoted to Production
Assets; they stay as visual-reference reproductions.

### 2. Added missing production metadata

Two production assets created in earlier work did not yet have
`metadata.json` sidecars, so `ProductionAssetLibrary` could not discover them:

| Figure Type | Asset kind | Production ready | Notes |
|---|---|---|---|
| `ScatterRegressionRaincloud` | template | true | Long-format CSV `y,x,group`; COPY-FIRST friendly |
| `GroupedBarChart` | template | true | Long-format CSV `marker,value,facet`; COPY-FIRST friendly |

This makes the Phase 4 metadata system consistent for all Python templates
added after the initial pilots.

### 3. New regression benchmark

`scripts/regression_benchmark.py` runs a fixed set of 8 real-task cases with
synthetic data and deterministic seeds. It verifies:

- `figure_type` resolves correctly
- `ProductionAssetLibrary` returns a reasonable asset kind
- `ReferenceLibrary` returns a matching visual reference (when one exists)
- Palette source follows the documented priority: explicit > reference > default
- PNG output is generated and passes basic QA (exists, non-empty, PNG header)
- A Visual Source Report field set is produced for each case

Cases:

| Case | Figure Type | Production Asset | Visual Reference | Palette | Runtime | Result |
|---|---|---|---|---|---|---|
| grouped_violin | GroupedViolin | template | `4d2c99dd4a107724` | summer_beach | Python | PASS |
| heatmap | heatmap | reusable | `3b94fea2e7f95f8f` | fresh_holiday | Python | PASS |
| pca | PCA | example | None | N/A | R | WARN (R not installed) |
| marginal_density | MarginalDensity | template | `387e55d62c99c422` | soft_forest | Python | PASS |
| stacked_bar_scatter | StackedBarScatter | example | `daaa5c61d74703b8` | summer_beach | Python | PASS |
| grouped_bar_chart | GroupedBarChart | template | `44d7a697ee30c4ac` | pastel_girl | Python | PASS |
| bar_categorical | BarCategorical | None (VR only) | `76866da267962098` | None | Python | PASS |
| scatter_regression_raincloud | ScatterRegressionRaincloud | template | `55abd06fbf4dcbb9` | watercolor_bloom | Python | PASS |

The benchmark does **not** do pixel-perfect golden image comparison. It checks
structure, metadata, selection logic, output existence, and QA.

### 4. R runtime handling

The PCA case requires the existing `assets/figures/PCA/plot_PCA.R`. R is not
installed in this environment, so the case is marked `WARN` and render is
skipped. This is treated as an expected environmental gap, not a Python
workflow failure.

## Test results

All executed tests passed:

| Suite | Result |
|---|---|
| `python -m py_compile scripts/*.py` | OK |
| `python scripts/test_palette_manager.py` | 23/23 OK |
| `python scripts/test_reference_library.py` | 27/27 OK (1 skipped) |
| `python scripts/test_workflow_integration.py` | 28/28 OK |
| `python scripts/test_production_asset_manager.py` | 19/19 OK (1 skipped) |
| `python scripts/test_phase5_workflow.py` | 14/14 OK |
| `python scripts/e2e_smoke_test.py` | PASSED |
| `python scripts/check_references.py` | HEALTHY |
| `python scripts/run_ab_tests.py` | 21/21 (100%) |
| `python scripts/qa_coverage.py` | 26/26 (100%) |
| `python scripts/regression_benchmark.py` | 7 PASS / 1 WARN / 0 FAIL |

## What did NOT change

- No new embedding, CLIP, vector DB, or registry system
- No new manager or router layer
- No bulk ingestion of additional references
- No rewrite of SKILL.md workflow
- No modification of existing production scripts' visual output
- No pixel-perfect golden image tests

## Architecture Freeze

**Effective from this commit, academic-figure-skill is in architecture freeze.**

The following components are considered stable:

- `SKILL.md` workflow (create / revise / review / export / reference)
- `scripts/palette_manager.py` and `scripts/palettes.py`
- `scripts/reference_library.py`
- `scripts/production_asset_manager.py`
- `scripts/compose.py`
- QA scripts under `scripts/check_*.py` and `scripts/qa_validator.py`
- `references/directory-map.md`

**Principle going forward:**

> Only fix bugs or make the smallest possible adjustment required by an actual
> drawing task. Do not add new managers, new registries, new reference types,
> embedding systems, YAML configs, or additional abstraction layers unless a
> real use case proves they are necessary.

The next step is to use the skill for real papers and let concrete failures
drive the next phase.
