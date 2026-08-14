# Source Reconstruction Library Design

## Goal

Create one independently generated, reusable visual-grammar reconstruction for every raster figure in the licensed `nature-figure` collection and the license-unknown `figures4papers` collection, without copying source pixels or source plotting code.

## Scope and invariants

- Discover 15 licensed `nature-figure` images after excluding its bundled third-party subtree and 39 upstream `figures4papers` images: 54 unique source fingerprints.
- Create exactly one reconstruction record per source SHA-256.
- Store generated PNGs and their standalone rendering program in `assets/visual-references/generated-archive/` through `ReferenceLibrary`.
- Store only repository names, source-relative paths, dimensions, hashes, observable visual grammar, and reconstruction provenance. Never store local absolute paths.
- Treat Apache-2.0 `nature-figure` images as licensed visual sources. Treat `figures4papers` images as observation-only sources and use `independent_reconstruction` for every result.
- Preserve existing third-party reference entries. Do not duplicate, delete, promote, or silently relabel them.
- Generated pixels must not equal source pixels. Generated code must not import or quote source repository code.

## Components

`scripts/source_reconstruction_library.py` owns discovery, classification, deterministic rendering, archiving, manifest writing, and read-only validation. Its public functions accept explicit roots so tests and future updates do not depend on this machine's layout.

Discovery emits stable `SourceFigure` records. Classification uses path and filename semantics plus image aspect ratio to select a visual family. Rendering uses Matplotlib, NumPy, and Pillow with a SHA-derived seed. A compact family registry covers chart atlases, statistical plots, manifolds, microscopy/image plates, networks, mechanisms, and rich multi-panel composites. Each source gets its own title-free synthetic content and parameter variation.

The source-reconstruction manifest is the one-to-one audit index. Reference-library sidecars remain the truth for generated assets; the manifest links source fingerprints to archive IDs and records any pre-existing exact-copy reference ID found during the audit.

## Idempotence and errors

Before rendering, the builder reads the existing manifest by source fingerprint. If the archived image and sidecar still exist, it reuses the record. Missing or invalid outputs are regenerated. Discovery fails clearly when either source root is absent or when duplicate source fingerprints occur across the selected 54-image set.

## Verification

Unit tests cover discovery counts, relative provenance, licensing action, family classification, image non-identity, archive metadata, code independence, and idempotence. `check_source_reconstruction_library.py` validates the installed collection without requiring either source checkout. Full skill tests, skill-contract validation, reference-library validation, registry rebuild, and a contact-sheet inspection complete the gate.
