# ChartMimic index

This directory stores only a compact retrieval catalog derived from the external
[ChartMimic](https://github.com/ChartMimic/ChartMimic) benchmark. The benchmark
checkout is kept outside the Skill at `E:\DATA\ChartMimic` and is not copied into
the package. Its records are useful for studying chart families, canvas ratios,
and chart-to-code evaluation; they are not production assets or a substitute for
opening a concrete reference image.

Refresh the catalog after updating the checkout:

```powershell
$py = "C:\Users\LRH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py scripts/chartmimic_catalog.py E:\DATA\ChartMimic\dimentions_info_edit.jsonl `
  --output assets/reference-benchmarks/chartmimic/catalog.json
```

The catalog stores IDs, chart-family hints, dimensions, aspect ratios, and a
source-record pointer. It intentionally does not duplicate ChartMimic code or
images.
