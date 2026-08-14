# Contributing

Thank you for improving Publication Figure Design.

## Development

Use Python 3.10+ and install dependencies from `requirements.txt`. From the repository root, run:

```bash
python -m unittest discover -s scripts -p 'test_*.py' -q
python scripts/check_skill_contract.py
python scripts/check_references.py
python scripts/check_source_reconstruction_library.py
python scripts/check_source_reference_catalog.py
```

Keep generated caches, local source checkouts, private reference images, and credentials out of commits. New bundled visual material must have clear redistribution provenance and a metadata record.

## Pull requests

Explain the user-visible behavior, include the checks you ran, and attach before/after evidence for visual changes. Contributions are accepted under the Apache License 2.0.
