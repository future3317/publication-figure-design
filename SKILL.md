---
name: publication-figure-design
description: "Design, reconstruct, revise, review, or export publication-grade scientific figures across research fields and venues."
---

# Publication Figure Design

Create the requested figure, not a paperwork trail. Work directly on the figure source and render unless the user specifically needs a resumable PFD session. The `pfd` CLI manages task/session metadata and QA; it does not draw the figure, so running it is not a substitute for editing, rendering, or inspecting the output.

## The working loop

1. Identify the scientific message, data, labels, uncertainty, target size, and requested deliverable from the user's files and brief. Ask only for information that is truly missing; do not make up data or turn a clear task into a form-filling exercise.
2. Decide the visual structure before touching style: what is the focal evidence, what are the panels, and what marks/relationships express the data truthfully? Preserve scientific meaning. For revisions, inspect the current render and source, but do not preserve their layout, palette, or code pattern unless they still serve the task.
3. Use references when they add evidence. Always inspect a user-supplied reference. If none is supplied, retrieve a small, relevant set only when the task needs visual direction; inspect the actual images and select by structural fit before style. For a requested match, identify a few visible targets (panel topology, mark/arrow grammar, palette roles, labels/legend, and spacing) and verify them in the render. A reference controls visual grammar, never scientific content; never copy its scientific content.
4. Implement or restructure the source, render the requested figure, and inspect the actual output at intended publication size. Before delivery, confirm scientific meaning and labels are intact, text and encodings are legible and accessible, and the requested export format and dimensions are met. Fix visible problems (especially wrong structure, overlap/clipping, unreadable text, weak contrast, confusing encodings, and cramped spacing), then render again. Do not claim completion from source code or a QA JSON alone.
5. Deliver the figure and reproducible source when available, with a brief note of any genuine limitation. Do not emit internal checklists or reports unless requested.

## Global visual rules — apply on every figure

- Prefer soft segmentation, short evidence-led titles, clear text hierarchy, generous but purposeful whitespace, and restrained legends/annotations.
- Use low-saturation semantic colors with sparse accents, but keep text and critical marks strongly contrasted. Never place pale text on a pale fill; choose text color against the actual local background.
- Choose marks and connections that state the real relationship: connect only genuinely paired/ordered data; distinguish observations, estimates, uncertainty, and reference lines; arrows must have clear direction, weight, path, and endpoints.
- Make every panel and annotation earn its space. Preserve scientific semantics and complete data; never alter values, uncertainty, scales, or labels to make the design look cleaner.
- When a reference or user preference conflicts with scientific truth, accessibility, or explicit requirements, preserve the higher-priority constraint and explain the visible deviation briefly.

## Load only what this task needs

- Concrete image matching or reference reconstruction: [reference-driven-reconstruction.md](references/reference-driven-reconstruction.md).
- Choosing a chart for paired, continuous, independent, or operating-point data: [encoding-and-uncertainty.md](references/encoding-and-uncertainty.md).
- TeX/TikZ/PGFPlots output: [tex-rendering.md](references/tex-rendering.md).
- Reference intake, benchmark, or champion maintenance: follow [runtime-and-evaluation.md](docs/maintenance/runtime-and-evaluation.md).

Use the project's `piepaper` interpreter when running its Python scripts; see [runtime-environment.md](references/runtime-environment.md). Do not run reference-local code during intake.
