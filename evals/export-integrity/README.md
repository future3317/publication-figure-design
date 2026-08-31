# Export integrity eval suite

Tests that exported files preserve fonts, layers, metadata, and provenance.

## Tasks

- `missing_embedded_font`: vector exports must embed fonts.
- `missing_figure_manifest`: publication package must include figure-manifest.json.
- `wrong_dpi`: raster exports must match declared DPI.

See `tasks.jsonl`.
