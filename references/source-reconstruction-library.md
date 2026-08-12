# Source Reconstruction Library

Use this route only when maintaining the bundled source-by-source visual-grammar archive. Ordinary figure creation should query the reference library and inspect at most three candidates.

## Contract

Each audited source image has one SHA-256 fingerprint, one observable visual family, one independently rendered PNG, and one generated-archive sidecar. Reconstruct panel topology, mark geometry, layer relationships, palette roles, density, whitespace, and annotation patterns; use synthetic data and original code. Never copy source pixels, trace labels, import source scripts, or make either source checkout a runtime dependency.

The manifest at `assets/visual-references/source-reconstruction-manifest.json` is the audit index. It records repository-relative source paths, dimensions, license class, source action, generated archive ID, and any pre-existing exact-copy reference found during the audit. Sidecar metadata remains the archive truth.

## Commands

Validate the installed archive without source repositories:

```bash
python scripts/check_source_reconstruction_library.py
```

Rebuild after an explicitly requested source audit:

```bash
python scripts/source_reconstruction_library.py build \
  --nature-root <nature-figure-root> \
  --figures-root <figures4papers-root>
```

Run the builder twice. The second run must report `created_count: 0`. Then rebuild the reference registry, run the lightweight checker, and inspect a contact sheet spanning every visual family. Do not promote an entry to a production asset solely because reconstruction validation passes.
