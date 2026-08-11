# Phase 5.1 Migration Report: Merge Scientific Figure Making

## Goal

Migrate useful content from the local `scientific-figure-making` skill into
`academic-figure-skill`, eliminate duplicate/old skill copies, and add a few
synthetic visual references based on the figures4papers house style.

## What was merged

### Text references

1. `references/publication-style-patterns.md` (new)
   - Ultra-wide aspect ratios for multi-metric panels
   - Dedicated legend panel
   - Categorical bars without x-tick labels
   - Dynamic y-axis scaling
   - Print-safe bar separation (edges + hatch)
   - Semantic color roles
   - Alpha-based ablation encoding
   - Direct bar annotation

2. `references/multipanel-layout.md` (updated)
   - Added "Practical Layout Patterns" section covering dedicated legend panels
     and ultra-wide single-row layouts.

3. `references/common-pitfalls.md` (updated)
   - Added "Axis Range Traps" (dynamic y-axis scaling).
   - Added "Print-Safe Bar Encoding" (edges/hatch).

### Visual references

The original `scientific-figure-making` skill had no local example images; its
demos are links to the `figures4papers` GitHub repository. To satisfy the user's
request to add example figures to the library, three synthetic redraws were
generated and ingested:

| ID | Figure type | Subtype | Tags |
|---|---|---|---|
| `ed6bbae45d17df9c` | BarComparison | figures4papers_grouped_bar | figures4papers, publication-style, grouped-bar, annotation, semantic-colors |
| `8c7c60af478ae5d0` | LineTrend | figures4papers_trend_legend_panel | figures4papers, publication-style, line-trend, multi-panel, dedicated-legend |
| `e52120014b49abe8` | heatmap | figures4papers_heatmap | figures4papers, publication-style, heatmap, magma, correlation |

All three are marked `usage_scope: redistributable` because they are synthetic
made-up-data redraws, not paper screenshots.

## What was deleted

- `C:/Users/LRH/.codex/skills/academic-figure-skill-old-backup`
  - Stale duplicate of academic-figure-skill; backed up earlier and now removed.
- `E:/CODE/figures4papers/scientific-figure-making`
  - The skill being migrated; its useful content is now in academic-figure-skill.

## What was NOT changed

- No existing production scripts modified.
- No changes to palette manager, production asset manager, or reference library
  logic.
- No changes to SKILL.md main workflow.

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
| `python scripts/check_references.py` | HEALTHY |
| `python scripts/run_ab_tests.py` | 21/21 (100%) |
| `python scripts/qa_coverage.py` | 26/26 (100%) |

One Phase 5 test was slightly adjusted because adding the new heatmap reference
changed the result count; the test now asserts that the expected reference is
present and ranked first rather than assuming a single result.

## Current skill location

The single authoritative copy is now:

```
C:/Users/LRH/.agents/skills/academic-figure-skill
```

Configure Codex / Claude Code / other agents to read this path.
