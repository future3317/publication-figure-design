# Asset Adaptation Contract

Use this whenever considering bundled production code, an archived example, or prior plotting code.

## Required field map

Write this table before editing the candidate implementation:

| Candidate field | User field | Semantic role | Unit | Allowed/domain values |
|---|---|---|---|---|

Also state:

- grouping field and display order;
- biological/technical replicate unit;
- center statistic;
- spread or interval definition;
- missing-data predicate and before/after row and replicate counts;
- transform domain assumptions.

No mapping means no reuse. Do not select convenient columns merely to make an example execute.

## Four adaptation levels

### `exact_reuse`

Require affirmative evidence for all five dimensions:

1. panel topology;
2. mark geometry;
3. layer topology;
4. data encoding;
5. annotation/legend model.

Change only data paths/mappings and parameters already declared adaptable. Run the copied implementation on representative real input. If it fails or the visual grammar changes, reclassify; do not patch it into nominal reuse.

### `structural_adaptation`

Use when the chart family and scientific encoding match but one or more structural dimensions differ. Name the layout, axes, mark, layer, or legend functions that will be replaced. Palette/font/alpha/line-width changes alone never qualify.

### `style_only`

Use when dimensionality, chart family, or visual grammar differs. Borrow only compatible tokens such as semantic palette roles, type hierarchy, whitespace ratios, or annotation treatment. Do not retain old panels or layers.

### `build_new`

Use when neither structure nor reusable style tokens serve the contract. Build from the evidence chain and backend conventions.

## Semantic and transform guards

- A 2D joint-density asset is not a multi-variable 1D distribution asset.
- A log-scale asset is incompatible with non-positive values until the scientific transform decision changes explicitly.
- A sequential palette is not a categorical palette.
- Random/demo values must be unreachable from the production entrypoint.
- Interpolation coordinates must be strictly monotone; reverse coordinates and values together.
- Labels above summaries must clear `center + spread`, not only the center.

## Internal evidence record

Record candidate path/ID, adaptation level, field map, compatibility evidence, changed structures, runtime result, and output path in an internal source header or QA artifact. User-facing summaries follow `privacy-provenance.md`.
