# Publication Figure Design adapter — OpenAI Codex

This is a thin loader for `publication-figure-design` manifest version `4.0.0`.
The canonical instructions and route contracts live in the bundled skill; this
file is not a replacement or a second source of design rules.

Runtime bundle:
- `SKILL.md`
- `manifest.yaml`
- `references/`
- `scripts/`
- `src/`
- `assets/visual-references/`
- `assets/visual-references/**/reference_dna.json`
- `assets/reference-benchmarks/`
- `assets/anti-pattern-atlas/`
- `assets/registry.jsonl`
- `schemas/`
- `indexes/`
- `profiles/`
- `evals/`
- `rules/`
- `sources/registry.yaml`

Generated: 2026-08-31 10:48 UTC

Load `SKILL.md` as the instruction entrypoint. When a route names a script,
schema, index, or reference asset, use the bundled relative path; do not
substitute an adapter-local copy.
