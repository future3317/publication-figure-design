# Backend Selection

## Selection order

Choose the plotting backend in this order:

1. explicit user request;
2. workflow requirement, such as a required R-only package or an existing source the user asked to revise;
3. saved preference from `scripts/backend_preference.py get`;
4. Python default.

Save a preference only after an explicit user choice:

```bash
python scripts/backend_preference.py set python
python scripts/backend_preference.py set r
python scripts/backend_preference.py set tex
```

## Execution contract

A single-backend figure uses the selected backend for plotting, preview, vector/raster export, and visual-QA renders. If its runtime or a required package is missing, report the blocker and stop that render path. Do not silently generate a substitute in another language.

## TeX / TikZ / PGFPlots

Treat `tex` as a first-class backend. Read `references/tex-rendering.md` before
writing or revising `.tex` sources. Select PGFPlots for quantitative plots and TikZ
for schematics/geometry; both may be assembled in one TeX source. Declare the engine
(`lualatex`, `xelatex`, or `pdflatex`), package/compatibility versions, build directory,
and final assembler in `RenderPlan`. A missing compiler or package blocks this route;
Python/R substitution is not a successful render.

The TeX source, generated data inputs, compile log, PDF font evidence, and final-size
PNG are part of the reproducibility chain. Compile non-interactively with `-halt-on-error`
and keep unrestricted shell escape disabled unless a specific, allowlisted local helper
is required and recorded.

## Mixed mode

Mixed Python/R panels are allowed only when explicitly requested or a real panel capability requires them. Before rendering, declare:

| Panel | Backend | Required capability | Intermediate format |
|---|---|---|---|

Then name exactly one final assembler. The assembler may place rendered panels but must not redraw a selected-backend panel with another plotting backend. Use vector intermediates when feasible; if raster intermediates are necessary, render them at their final physical size and sufficient resolution.

If one panel runtime is missing, report that panel as blocked. Do not label a partial or cross-backend substitute as the completed figure.
