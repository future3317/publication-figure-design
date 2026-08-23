# Contributing

Thank you for improving Publication Figure Design.

## Development

Use the project Conda environment `piepaper` for all repository commands. On the
maintainer workstation its interpreter is `D:\Anaconda\envs\piepaper\python.exe`.
Install dependencies there, never in Conda `base`, and run from the repository root:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" -m unittest discover -s scripts -p 'test_*.py' -q
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_skill_contract.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_references.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_source_reconstruction_library.py
& "D:\Anaconda\envs\piepaper\python.exe" scripts/check_source_reference_catalog.py
```

For deterministic local execution, call the interpreter directly:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/ci_gate.py
```

Keep generated caches, local source checkouts, private reference images, and credentials out of commits. New bundled visual material must have clear redistribution provenance and a metadata record.

## Pull requests

Explain the user-visible behavior, include the checks you ran, and attach before/after evidence for visual changes. Contributions are accepted under the Apache License 2.0.
