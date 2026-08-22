# Runtime environment

All publication-figure rendering, reference reconstruction, image analysis, visual QA,
benchmark, and lifecycle commands in this repository use the project Conda environment
`piepaper`.

On this workstation the interpreter is:

```text
D:\Anaconda\envs\piepaper\python.exe
```

Prefer the explicit interpreter path (or the activated `piepaper` environment):

```powershell
conda activate piepaper
python scripts/ci_gate.py
```

For automation that must not depend on shell activation:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/ci_gate.py
```

Do not run this workflow with Conda `base`, an unrelated project environment, or the
system Python. If the environment is missing a required package, install it into
`piepaper` or report the missing dependency; do not silently fall back to another
interpreter. The environment itself is local machine state and must never be committed.
