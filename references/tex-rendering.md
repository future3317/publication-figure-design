# TeX / TikZ / PGFPlots rendering

Use the TeX backend when the figure benefits from native TikZ/PGFPlots geometry,
manuscript-matched typography, or an editable vector PDF. TeX is a renderer choice,
not a license to change the scientific contract: the same `TaskSpec`, `BindingMap`,
`StyleSpec`, `RenderTrace`, and final-size QA apply as for Python and R.

## Backend decision

- Use **PGFPlots** for quantitative axes, curves, scatter, bars, intervals, heatmaps,
  and colorbars; use **TikZ** for schematics, arrows, nodes, geometric overlays, and
  panel assembly. They may be combined in one `.tex` source with one final assembler.
- Prefer `lualatex` or `xelatex` when the manuscript requires system/OpenType fonts;
  use `pdflatex` only with a deliberate legacy-font policy. Record the selected engine
  and version in `RenderPlan`/`ExportManifest`.
- If the requested TeX compiler or package is unavailable, stop the TeX render path
  and report the missing capability. Do not silently substitute Python or R.

## Reproducible source contract

Keep the `.tex` source, any generated data tables, local style files, and a clean
compile command beside the render artifact. Pin `pgfplots` compatibility (for example
`\pgfplotsset{compat=1.18}` when that version is installed), declare the color roles,
units, axis domains, layer order, and uncertainty meaning in the source or its
machine-readable packet. Generate data from the bound source; do not type values into
TikZ coordinates merely to imitate a reference image.

Compile with a non-interactive, fail-fast command such as:

```text
lualatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=<build> figure.tex
```

Use a temporary build directory and retain the `.log`/`.fls` evidence outside the
delivery bundle. Unresolved `Overfull \\hbox`, `Overfull \\vbox`, undefined references,
missing glyphs, and package errors are QA findings—not harmless console noise.

Do not enable unrestricted `--shell-escape` or `\write18`. If PGF externalization or
another helper genuinely needs a subprocess, use an explicit local allowlist, fixed
build directory, timeout, and recorded command; otherwise keep shell escape disabled.

## Layout and visual grammar

- Bind `width`, `height`, `\linewidth`/`\columnwidth`, panel gaps, and text sizes to
  the target physical dimensions. Inspect the compiled PDF and a final-size PNG; a
  scaled browser preview does not pass.
- Route arrows and connectors around labels, curves, insets, and nodes. Give callouts
  an explicit anchor and cleared offset; use `on background layer`/`preaction` or a
  local backing only when it preserves the reading path.
- Keep PGFPlots layers intentional (`axis on top`, `set layers`, draw order), and
  separate raw points, declared trends, uncertainty bands, reference lines, and key
  markers. Do not let translucent fills or dense nodes become an opaque mixed block.
- Use one compact legend or direct labels. Do not repeat method names in legend,
  panel title, node text, and axis categories without distinct reading jobs.

## Typography and export

Use the same font policy as the manuscript, keep the active hierarchy at final size,
and verify embedded fonts with `scripts/audit_pdf_text.py` plus the platform PDF/font
inspection available in the QA environment. Preserve vector text and strokes in the
PDF; rasterize only embedded image layers. Export the editable PDF (and SVG/TikZ source
when requested) together with a PNG preview at the declared physical dimensions and
resolution. Reopen the output and check page geometry, clipping, color contrast,
annotation clearance, and text-on-fill contrast before marking `Export` complete.

## TeX-specific failure checklist

Before delivery, record pass/fail for: compiler/package availability; compile log; page
size; font embedding/glyphs; overfull boxes; axis and mark clipping; panel/inset
alignment; legend and annotation collisions; shell-escape policy; and source/data
provenance. A TeX PDF that compiles is not automatically a publication-ready figure.
