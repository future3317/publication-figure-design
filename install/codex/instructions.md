# Publication Figure Design adapter — OpenAI Codex

This is a thin loader for `publication-figure-design` manifest version `2.1.0`.
The canonical instructions and route contracts live in the bundled skill; this
file is not a replacement or a second source of design rules.

Runtime bundle:
- `SKILL.md`
- `manifest.yaml`
- `references/`
- `scripts/`
- `src/`
- `assets/visual-references/`
- `assets/registry.jsonl`
- `schemas/`
- `indexes/`

Generated: 2026-08-18 17:50 UTC

Load `SKILL.md` as the instruction entrypoint. When a route names a script,
schema, index, or reference asset, use the bundled relative path; do not
substitute an adapter-local copy.
