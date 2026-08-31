# Reference selection eval suite

Tests whether the reference retrieval system returns semantically appropriate
references for a given scientific task, not just visually similar pixels.

## Tasks

- `paired_operating_point`: query for paired seed comparison should return paired references.
- `classification_diagnostics`: query for ROC/calibration should return classification diagnostics.
- `avoid_wrong_family`: a bar-chart query should not return a trend family reference.

See `tasks.jsonl`.
