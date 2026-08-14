# Phase 4 Implementation Report: Production Asset Metadata + Promotion MVP

## Goal
Add a thin metadata layer so agents can quickly decide whether a production asset is safe to COPY-FIRST or only useful as visual inspiration, without reading hundreds of lines of script. Pilot with 5 representative figure types.

## What changed

### New files

1. `references/production-asset-metadata.md`
   - Schema reference and agent usage rules for `assets/figures/<type>/metadata.json`.
   - Defines `asset_kind`: `template`, `reusable`, `example`.
   - Describes promotion path from Visual Reference → Production Asset.

2. `scripts/production_asset_manager.py`
   - `ProductionAsset` — in-memory metadata object.
   - `ProductionAssetLibrary` — scan/get/list/query/validate/promote API.
   - Promotion helper copies a reviewed, production-ready visual reference into `assets/figures/<type>/` and writes a metadata sidecar.
   - CLI: `scan`, `list`, `query`, `validate`, `promote`.

3. `scripts/test_production_asset_manager.py`
   - 19 unit tests covering validation, discovery, filtering, query sorting, promotion, and rejection gates.

4. Pilot production metadata sidecars:
   - `assets/figures/GroupedViolin/metadata.json` → `template`
   - `assets/figures/MarginalDensity/metadata.json` → `template`
   - `assets/figures/heatmap/metadata.json` → `reusable`
   - `assets/figures/StackedBarScatter/metadata.json` → `example`
   - `assets/figures/PCA/metadata.json` → `example`

### Modified files

5. `scripts/__init__.py`
   - Exports `ProductionAsset`, `ProductionAssetLibrary`, `PRODUCTION_METADATA_FIELDS`.

6. `SKILL.md`
   - Step 4 now instructs agents to read `metadata.json` first when present.
   - Added a metadata shortcut decision block before the full COPY-FIRST tree.
   - Added `references/production-asset-metadata.md` to the references table.

## What did NOT change

- No existing production script was modified.
- No bulk metadata migration for the other 24 figure types.
- No changes to Visual Reference schema or palette manager.
- No embedding, vector DB, or theme manager refactor.

## Promotion workflow

```
Visual Reference
    → review_status="reviewed" + production_ready=true
    → ProductionAssetLibrary.promote_from_visual_reference(ref_id)
    → copies image + code to assets/figures/<type>/
    → writes metadata.json
    → original reference stays in visual-references/ for provenance
```

Only reviewed + production-ready references can be promoted. The gate is enforced by raising `ValueError`.

## Test results

All executed tests passed:

| Suite | Result |
|---|---|
| `python -m py_compile scripts/*.py` | OK |
| `python scripts/test_palette_manager.py` | 23/23 OK |
| `python scripts/test_reference_library.py` | 27/27 OK (1 skipped) |
| `python scripts/test_workflow_integration.py` | 28/28 OK |
| `python scripts/test_production_asset_manager.py` | 19/19 OK (1 skipped) |
| `python scripts/e2e_smoke_test.py` | PASSED |
| `python scripts/check_references.py` | HEALTHY |
| `python scripts/run_ab_tests.py` | 21/21 (100%) |
| `python scripts/qa_coverage.py` | 26/26 (100%) |

Skipped tests are package-import checks that cannot be verified when the test file is run directly; they pass when run as `python -m scripts.test_*`.

## Pilot metadata summary

| Figure type | asset_kind | runtime | production_ready | Rationale |
|---|---|---|---|---|
| GroupedViolin | template | python | true | Reusable function with clear parameters. |
| MarginalDensity | template | python | true | Reusable function driven by CONFIG dict. |
| heatmap | reusable | python | true | Multiple scripts; require data replacement. |
| StackedBarScatter | example | python | false | Hard-coded 3-group demo data. |
| PCA | example | r | false | Tightly coupled to metabolite input files. |

## Next phase recommendation

Phase 5 should run real tasks end-to-end with the new metadata in play: verify that agents actually read `metadata.json`, choose COPY-FIRST vs. visual adapt correctly, and record production asset sources accurately. Only after the pilot metadata proves useful should it be rolled out to more figure types.
