---
name: academic-figure-skill
description: "Create, reconstruct, revise, review, and export publication-grade scientific figures for Nature/Cell/Science-family manuscripts. Use for static manuscript plots, multi-panel figures, concrete visual-reference matching, journal figure QA, and vector/raster delivery. Do not use for interactive dashboards, exploratory analysis without publication intent, statistics-only work, data cleaning, literature review, PowerPoint, or image editing without figure assembly."
---

# Academic Figure Skill

Build a scientific argument, not a decorated template. Scientific truth is immutable; a concrete visual reference controls the visual grammar after that.

## Dispatch

Choose one mode, then apply the concrete-reference gate independently.

| Mode | Use when | Route |
|---|---|---|
| **create** | Make a new manuscript figure from data or a stated claim | `references/workflow-create.md` |
| **revise** | Change an existing figure or plotting source | Read the existing artifact; run only affected creation stages, then QA |
| **review** | Assess reviewer readiness or diagnose visual weaknesses | `references/checklist.md` and `references/revision-cases.md` |
| **export** | Change dimensions, format, resolution, or journal target | `references/delivery-contract.md` and `references/export-specs.md` |
| **reference** | Store, query, or archive visual references | `references/visual-reference-library.md`; use `scripts/reference_library.py` |

Do not force revise, review, export, or reference work through the full create route.

## Immutable precedence

Use this order whenever constraints compete:

1. scientific meaning, complete data, and non-misleading encoding;
2. explicit user requirements;
3. concrete reference structure and visual language;
4. compatible implementation material;
5. skill defaults.

Existing code is implementation material, never a design constraint. A production-quality old script is still incompatible if it preserves the wrong visual skeleton.

## Core figure contract

Before implementation, establish these five points from `references/figure-contract.md`:

1. one-sentence core conclusion;
2. evidence chain, with one unique job per panel;
3. figure archetype and panel hierarchy;
4. plotting backend per panel and final assembler;
5. journal, physical dimensions, and export bundle.

Use a full contract for create/major revision, an abbreviated conclusion/evidence contract for a small revision, and no new contract for a purely cosmetic edit. If the user provides data but no scientific question or requested chart, ask what the figure must show before designing it.

## Concrete-reference gate

Activate `reference-driven` mode whenever the user supplies, selects, points to, or explicitly asks to match a concrete image. A palette name or broad phrase such as “Nature style” alone does not activate it.

Before selecting old code or an asset:

1. Open every concrete reference and inspect the actual pixels. Do not rely on filenames, tags, metadata, or memory.
2. Read `references/reference-driven-reconstruction.md` and write its Reference Reconstruction Contract.
3. Record observable `must_match` features and scientific/data reasons for allowed deviations.
4. Classify both the reference decision and the unified adaptation level below.

Do not continue if the reference cannot be opened. Do not call palette-only, font-only, alpha-only, line-width-only, or marker-size-only changes a reconstruction.

## Unified adaptation ladder

Apply this one taxonomy to user references, archived examples, and production assets. Read `references/asset-adaptation.md` before selecting implementation material.

| Level | Required compatibility | Action |
|---|---|---|
| `exact_reuse` | panel topology, mark geometry, layer topology, data encoding, and annotation/legend model all match | Reuse the implementation; change only mapped data and declared parameters |
| `structural_adaptation` | chart family and scientific encoding match, but at least one structural dimension differs | Replace incompatible layout, axes, layers, geometry, or legend code |
| `style_only` | structure/dimensionality differs but visual tokens remain relevant | Borrow only compatible palette roles, typography, spacing, or annotation treatment |
| `build_new` | no compatible structural or stylistic source exists | Build a new implementation around the figure contract |

Reference-decision mapping:

- `reuse` requires `exact_reuse` and evidence for all five dimensions.
- `restructure` requires `structural_adaptation` and explicit non-cosmetic changes.
- `rewrite` requires `style_only` or `build_new`; never retain irrelevant old panels, layers, legends, or annotations.

Select implementation material only after this classification. Convenience, familiarity, and prior code quality are not compatibility evidence.

## Backend gate

Read `references/backend-selection.md`. Resolve the plotting backend in this order: explicit request → workflow requirement → saved preference → Python default. Use `scripts/backend_preference.py` to read or save an explicit preference.

A normal figure uses one plotting backend for plotting, preview, export, and visual QA. Mixed Python/R mode is allowed only when the user requests it or a real panel capability requires it. Declare the backend for every panel and exactly one final assembler. Never silently substitute another backend when the selected runtime or package is missing; stop that render path and report the blocker.

## Data and transformation gate

Preserve all user-provided observations unless the user authorizes a scientifically justified subset. Solve rendering scale with rasterized marks, density views, or disclosed aggregation—not convenience sampling.

Before adapting code, write the field mapping required by `references/asset-adaptation.md`: template field, user field, semantic role, unit, allowed values, group field, replicate unit, center, and uncertainty definition. Record exact before/after row and replicate counts for every exclusion. Preserve the source file.

Check inherited transforms against the real data domain. Never silently remove non-positive values for a log scale, invent a pseudocount, reverse interpolation inputs incorrectly, or allow simulated/example data to execute in a production path. Use `scripts/figure_safety.py` for monotone interpolation and uncertainty-aware label placement where applicable.

## Create loop

For create or major revision, execute `references/workflow-create.md`:

1. establish the figure contract;
2. inspect data only in service of the scientific question;
3. activate and complete the concrete-reference gate when applicable;
4. resolve backend and runtime;
5. select the adaptation level and map fields;
6. implement at the final physical dimensions;
7. render, inspect, fix, and rerender;
8. validate and deliver.

Use `scripts/compose.py` for multi-panel assembly when compatible. Use `scripts/reference_library.py` only for optional visual-reference retrieval when no concrete reference was selected. User colors outrank user palettes; both outrank an optional library reference and defaults. A visual reference never changes scientific semantics.

## Render and QA gate

Before delivery:

1. Run `scripts/qa_validator.py` on final plotting source and resolve every FAIL.
2. Render only with the declared backend(s) and final assembler.
3. Run `scripts/audit_pdf_text.py <figure.pdf> --min-pt 5` on the vector master.
4. Inspect every panel and the assembled figure at final physical size using `references/checklist.md`.
5. When reference-driven, create an equal-size reference/candidate comparison and run `scripts/check_reference_fidelity.py`. A FIX verdict blocks a claim of fidelity.
6. Run `scripts/check_skill_contract.py` only when maintaining this skill, not for each figure.

Static checks do not prove that statistics, scientific meaning, or rendered composition are correct. Visual inspection remains mandatory.

## Delivery

Follow `references/delivery-contract.md`, `references/figure-legend-contract.md`, and `references/privacy-provenance.md`. Deliver the requested plotting source, editable vector master, high-resolution raster/preview, compact QA report, and the statistics/source-data facts needed by the legend.

Keep exact asset paths, private filenames, template IDs, and working provenance in internal source headers or QA artifacts. Do not expose them in an ordinary user-facing summary unless the user asks.

## Resource routes

`manifest.yaml` is the declarative routing index. Read only the references required by the active route; do not load the whole library.

| Condition | Read or run |
|---|---|
| Always for create/major revision | `references/figure-contract.md`, `references/workflow-create.md` |
| Concrete reference | `references/reference-driven-reconstruction.md`; run `scripts/check_reference_fidelity.py` |
| Asset/example reuse | `references/asset-adaptation.md`, `references/directory-map.md`, `references/production-asset-metadata.md` |
| Backend choice or mixed panels | `references/backend-selection.md`; use `scripts/backend_preference.py` |
| Python plotting | `references/matplotlib.md`, `references/typography.md`, `references/color-palettes.md` |
| R plotting | `references/r-rendering.md`; add `references/complexheatmap.md` only for ComplexHeatmap |
| Multi-panel assembly | `references/multipanel-layout.md` |
| Target journal | `references/journal-specs.md`, then `references/journal-intel.md` when journal-specific evidence is needed |
| Export/delivery | `references/export-specs.md`, `references/delivery-contract.md`, `references/figure-legend-contract.md` |
| QA/review | `references/checklist.md`, `references/common-pitfalls.md`; add `references/revision-cases.md` for reviewer simulation |
| Optional reference library | `references/visual-reference-library.md`; use at most 3 candidates |

Do not use or import any unlicensed third-party example collection. Production assets under `assets/` remain implementation candidates and never override the adaptation gate.
