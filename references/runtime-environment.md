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

## Matplotlib style baseline

The typography, palette-role, and export baselines in
`references/typography.md`, `references/color-palettes.md`, and
`references/export-specs.md` are sufficient to render a submission-ready figure.
`scienceplots` may be used to register the optional `science`, `ieee`, and
`no-latex` Matplotlib style sheets, but it must not be the sole source of visual
semantics. A renderer using it should retain the explicit baseline and fall back to
Matplotlib's built-in style if the package is unavailable; it must not change
scientific encodings, font sizes, palette roles, physical dimensions, or export
settings in that fallback.

When an offline source archive is supplied, install it only into `piepaper`.
If build isolation tries to download unavailable build tools and the package is a
pure Python style package, copying its verified import package into `piepaper`'s
`Lib/site-packages` is an acceptable local installation route. Verify the resulting
installation with `python -c "import scienceplots; print(scienceplots.__file__)"`.
