# Source Reconstruction Library

Use this route only when maintaining the bundled source-by-source visual-grammar archive. Ordinary figure creation should query the reference library and inspect at most three candidates.

## Contract

Each audited source image has one SHA-256 fingerprint, one source-specific visual blueprint, one independently rendered PNG, and one generated-archive sidecar. A visual family is a retrieval label only; it cannot choose the renderer. The blueprint must name the panel mosaic, relative spans, every panel's mark/layer recipe, annotation model, and observed hierarchy. Reconstruct those features with synthetic data and original code. Never copy source pixels, trace labels, import source scripts, or make either source checkout a runtime dependency.

The builder is an archive generator, not a curator. Every generated record begins `pending`, unrated, and not production-ready. A generic renderer that guesses a panel grid or cycles stock mini-panels fails the contract. Build equal-size source/reconstruction sheets with `scripts/review_source_reconstructions.py`, then open every numbered pair individually (the contact sheet is only an index). For every source record write a pass or fail verdict, panel topology, mark/layer types, legends/annotations, hierarchy, whitespace, legibility, and comparison artifact. A failed review remains `pending`; only a pass with an explicit rating can become `reviewed`.

## Exact visual sources

For this private library, catalog original visual samples separately with `scripts/source_reference_catalog.py`. These entries have `reference_kind=exact_visual_source` and are visually reviewed in their own right; they can guide selection after review, but never serve as runnable implementation assets. They remain distinct from independent reconstructions so an agent cannot mistake a rough redraw for the original sample.

The manifest at `assets/visual-references/source-reconstruction-manifest.json` is the audit index. It records repository-relative source paths, dimensions, license class, source action, generated archive ID, and any pre-existing exact-copy reference found during the audit. Sidecar metadata remains the archive truth.

## Commands

Validate the installed archive without source repositories:

```bash
python scripts/check_source_reconstruction_library.py
python scripts/check_source_reference_catalog.py
```

Rebuild after an explicitly requested source audit:

```bash
python scripts/source_reconstruction_library.py build \
  --nature-root <nature-figure-root> \
  --figures-root <figures4papers-root>
```

Run the builder twice. The second run must report `created_count: 0`. Then rebuild the reference registry, run the lightweight checker, and inspect a contact sheet spanning every visual family. Do not promote an entry to a production asset solely because reconstruction validation passes.

For the installed generated archive itself, run the lifecycle audit after renderer or
dependency changes:

```bash
python scripts/audit_generated_reproductions.py --sync-previews --visual-inspected
python scripts/make_generated_reproduction_contact_sheet.py \
  assets/visual-references/review-evidence/generated-reproduction-contact-sheet.png
```

This executes every reference-local renderer, writes objective figure cards, creates
stored-vs-fresh render evidence, and keeps source-fidelity review separate from
code/preview determinism. With `--sync-previews`, it also refreshes generated
`output_sha256` values in `source-reconstruction-manifest.json` and rebuilds
`assets/registry.jsonl`; no separate hidden sync step is required.

For a complete source audit, then run:

```bash
python scripts/review_source_reconstructions.py --nature-root <nature-figure-root> \
  --figures-root <figures4papers-root> --output-dir <review-dir>
python scripts/audit_source_reconstruction_batch.py --review-dir <review-dir>
python scripts/source_reference_catalog.py --nature-root <nature-figure-root> \
  --figures-root <figures4papers-root>
python scripts/audit_source_catalog_batch.py
```
