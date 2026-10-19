# Publication Figure Design

A scientific-figure design skill for research fields and publication venues. It helps Codex start from the scientific question and data, choose a truthful visual structure, use relevant visual references, edit or create reproducible source, and inspect the rendered figure.

References provide visual language only; they must not change data, statistical transforms, uncertainty, labels, or scientific conclusions.

## Use

Invoke the `publication-figure-design` Skill in Codex and describe the figure, data/source files, desired deliverables, and any references. For ordinary figure work, the agent directly inspects, edits, renders, and repairs the figure; no TaskSpec or `pfd run` session is required. The CLI manages resumable task sessions and QA metadata; it does not draw figures.

House style: soft segmentation, short titles, clear text hierarchy, structured whitespace, low-saturation semantic colors, and restrained legends/annotations. Text and critical marks must remain high-contrast. Scientific truth and explicit user requirements take precedence over style preferences.

## Repository

- [`SKILL.md`](SKILL.md): concise agent contract.
- [`references/`](references/): task-specific guides for reconstruction, encoding, uncertainty, and TeX.
- [`assets/visual-references/`](assets/visual-references/): references, analysis, and reproduction material.
- [`rules/`](rules/): machine-readable rules for programmatic QA.
- [`src/publication_figure_design/`](src/publication_figure_design/): contracts, design packets, optional session runner, and QA components.
- [`scripts/`](scripts/) and [`evals/`](evals/): reference maintenance, tests, evaluation, and release checks.

## Optional commands

Use the dedicated `piepaper` environment only when a resumable session or repository-maintenance feature is needed:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli run <task-spec.json>
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli reference ingest <image> <figure-type>
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli index build
& "D:\Anaconda\envs\piepaper\python.exe" scripts/ci_gate.py
```

`pfd run` does not render a figure and cannot replace inspection of the actual PNG/PDF. For TeX/TikZ/PGFPlots, read [`references/tex-rendering.md`](references/tex-rendering.md). Reference-library and evaluation procedures are in [`docs/maintenance/runtime-and-evaluation.md`](docs/maintenance/runtime-and-evaluation.md).

## Maintenance

Environment conventions are in [`references/runtime-environment.md`](references/runtime-environment.md). Never execute reference-local `code.py` during intake. Read [`AGENTS.md`](AGENTS.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md) before changing the repository.
