# Semantic correctness eval suite

Tests whether the system preserves scientific meaning when choosing encodings,
connectors, and panel order.

## Tasks

- `categorical_points_connected_as_line`: unordered categories must not be drawn as a trajectory.
- `inconsistent_axes`: related panels must share scale semantics.
- `channel_roles`: each visual channel must carry one semantic role.

See `tasks.jsonl`.
