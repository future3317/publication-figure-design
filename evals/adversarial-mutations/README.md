# Adversarial mutation eval suite

This suite intentionally introduces known bad practices into scientific figures
and records which rule violations a QA layer should detect.

## Purpose

- Provide reproducible "bad figure" examples.
- Link each mutation to concrete rule IDs from `rules/`.
- Measure how many violations can be detected automatically today vs. which still
  require manual or hybrid review.

## Structure

```text
cases/<mutation>/
├── generate.py              # matplotlib script that reproduces the bad figure
├── figure.png               # rendered mutation
├── task_spec.json           # what the user asked for
└── expected_violations.json # rule IDs that should be flagged
```

## Running

```powershell
PYTHONPATH=src D:\Anaconda\envs\piepaper\python.exe scripts/run_output_eval.py adversarial-mutations
```

## Current mutations

| Mutation | Category | Expected failures |
|---|---|---|
| tiny_font | publication-compliance | LAY-001, HOUSE-005 |
| missing_units | scientific-correctness | SCI-003 |
| wrong_errorbar_semantics | statistical-integrity | SCI-004 |
| mean_bar_hides_distribution | statistical-integrity | STAT-005 |
| lost_pair_identity | statistical-integrity | PAIR-001, STAT-002 |
| categorical_points_connected_as_line | semantic-correctness | PAIR-002, SEM-002 |
| wrong_colormap | accessibility | HOUSE-009, A11Y-001 |
| color_only_encoding | accessibility | A11Y-001 |
| low_contrast | accessibility | A11Y-002, A11Y-003 |
| legend_overlap | visual-clarity | LAY-002, ANN-002 |
| clipped_annotation | visual-clarity | LAY-004 |
| inconsistent_axes | visual-clarity | SCI-003, CMP-001 |

## Interpretation

A recall below 1.0 means the project still relies on manual/hybrid review for
that violation.  The suite is designed so that adding an automated detector
improves the reported recall.
