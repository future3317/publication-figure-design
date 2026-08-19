# Orchestrator contracts and lifecycle

The workflow is persisted as JSON under a task-local run directory. Every artifact has
`schema_version`, `contract_name`, and a path or inline payload that can be consumed by the
next stage. The Python implementations live in `src/publication_figure_design/contracts`
and `src/publication_figure_design/orchestrator`.
The shipped `pfd` CLI uses `orchestrator.runtime.build_runtime_orchestrator()`;
it invokes the image analyzer and reference comparator when task metadata supplies
paths, and records `not_provided` rather than claiming an absent source/render exists.

## State sequence

`Route → Intake → Reference Retrieval → Reference Inspection → Design Spec → Binding → Render → Compare → Critique → Repair → QA → Export`

The state machine records an input, output, gate result, attempt, and timestamps for every
stage. A failed gate sets the run to `blocked`; `retry` reruns the failed stage after repair,
`rollback` removes downstream artifacts, `resume` reloads the JSON session, and
`best_so_far` preserves the highest scored candidate across repair iterations.

Session telemetry is part of the persisted contract: `input_hash`, `reference_index_version`,
`selected_reference_ids`, `renderer_version`, `iterations`, `QA`, and `output_hash`. Resume
must reuse `selected_reference_ids` and the recorded index version; a changed corpus starts
a new session instead of silently changing the reference choice.

## Contract responsibilities

| Contract | Required content |
|---|---|
| `TaskSpec` | mode, objective, task id, requested outputs |
| `SourceSpec` | data/code/figure paths, scientific question, variable roles, uncertainty, provenance |
| `TargetSpec` | journal, physical dimensions, DPI, formats, minimum font, font condition |
| `ReferenceSet` | independent structure/style/component/annotation/palette roles and selection reason |
| `LayoutSpec` | panel topology, bboxes, reading order, plot/legend regions, whitespace and gaps |
| `StyleSpec` | palette, typography, strokes, markers, opacity, grid/spines, legend, annotation, spacing, density |
| `BindingMap` | target element → `match/restructure/rewrite/omit/add`, with no orphan series |
| `RenderPlan` | renderer per panel, backend, final assembler, raster/vector, variants, font fallback |
| `QAReport` | scientific/statistical/layout/typography/color/fidelity/accessibility/export gates and metrics |
| `ExportManifest` | final files, source files, QA report, provenance, formats, actual font used, substitution policy |

Do not promote a prose note, an agent declaration, or a reference-local script into a
stage artifact. A stage is complete only when its machine-readable output passes its gate.

In reference-led mode, `RenderPlan` must also contain `consumed_specs` with all four tokens:
`TypographySpec`, `PaletteSpec`, `LayoutSpec`, and `ComponentSpec`, plus
`style_spec_version` and `default_overrides_spec=false`. The renderer contract rejects a
plan that falls back to backend defaults.
