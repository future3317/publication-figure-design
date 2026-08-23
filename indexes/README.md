# Generated reference indexes

Reference indexes are derived from sidecar metadata and `assets/registry.jsonl`.
They are caches, never an additional source of truth, and adapters ship this
directory so retrieval routes have a stable runtime location.
`hybrid.json` is the active transparent index. It stores deterministic semantic,
structure and StyleDNA vectors plus provenance for optional SigLIP2/DINO adapters;
full-corpus NumPy search is the current default. `semantic.json` remains as a
derived compatibility view, not a production ranking source. The champion list is
an aesthetic upper-bound benchmark and never an automatic promotion rule.
