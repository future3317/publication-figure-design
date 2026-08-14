---
name: publication-figure-design
description: "Create, reconstruct, revise, review, and export publication-grade scientific figures for Nature/Cell/Science-family manuscripts, including multi-panel plots, paired operating-point comparisons, uncertainty-aware charts, concrete visual-reference matching, journal figure QA, and vector/raster delivery. Do not use for interactive dashboards, exploratory analysis without publication intent, statistics-only work, data cleaning, literature review, PowerPoint, or image editing without figure assembly."
---

# Publication Figure Design

Build a scientific argument, not a decorated template. Scientific truth is immutable; a concrete visual reference controls the visual grammar after that.

## Dispatch

Choose one mode, then apply the concrete-reference gate independently.

| Mode | Use when | Route |
|---|---|---|
| **create** | Make a new manuscript figure from data or a stated claim | `references/workflow-create.md` |
| **revise** | Change an existing figure or plotting source | Read the existing artifact; run only affected creation stages, then QA |
| **review** | Assess reviewer readiness or diagnose visual weaknesses | `references/checklist.md` and `references/revision-cases.md` |
| **export** | Change dimensions, format, resolution, or journal target | `references/delivery-contract.md` and `references/export-specs.md` |
| **reference** | Store, query, or archive visual references | `references/visual-reference-library.md`; use `scripts/reference_library.py`, `scripts/reference_reconstruction.py` for reference-local synthetic renderers, and `scripts/visual_evidence.py` through the fidelity gates |
| **library maintenance** | Audit or rebuild source-by-source visual-grammar reconstructions | `references/source-reconstruction-library.md`; run `scripts/audit_generated_reproductions.py`, `scripts/make_generated_reproduction_contact_sheet.py`, `scripts/check_source_reconstruction_library.py`, and `scripts/check_source_reference_catalog.py` |

### Single-image reference intake

When the user gives one image and says to save it to the reference library, treat that
image as a complete reference-intake task. The user does **not** need to provide
original source code, raw data, or a pre-existing figure-type label; the agent must
write a synthetic-data reconstruction after intake.

1. Open the actual pixels with the image viewer. Do not classify from the filename,
   surrounding prose, or a thumbnail alone.
2. Classify the visual family and normalized `figure_type`; for a heterogeneous plate,
   use the dominant assembly family and record the panel families in `notes` and tags.
   If the family is genuinely ambiguous, use `mixed_multi_panel` and explain the
   ambiguity instead of guessing a familiar chart.
3. Record the visual grammar: panel count/topology, hero-panel hierarchy, mark and
   encoding channels, layout, density, annotation/legend model, background, palette
   roles, and useful retrieval tags. Record the intended use as visual inspiration,
   not as a production implementation.
4. Record provenance. A user-supplied image defaults to `usage_scope=private_reference`
   and `license="user-supplied; redistribution not established"`. Use
   `usage_scope=redistributable` only when the user supplies a clear license or
   permission. Never infer public redistribution rights from the fact that an image
   was pasted into the conversation.
5. Run `python scripts/reference_library.py ingest <image> <figure_type> --metadata
   '<json>'`. Preserve the original source, use copy mode, and let the library assign
   the deterministic ID and sidecar path. Never hand-edit `assets/registry.jsonl`.
6. Add a reference-local `code.py` (or equivalent) that renders a synthetic-data
   reconstruction of the recorded visual grammar, plus its `reconstruction.png`
   preview. Original source data/code is not required; the reconstruction must be
   runnable and should reproduce topology, marks, hierarchy, palette roles, and
   annotation treatment closely enough to guide production work.
   Generate a companion `figure_card.json` with
   `scripts/reference_image_analysis.py analyze`; it records objective pixel evidence
   while leaving panels, axes, typography, and annotations explicitly
   `manual_required`.
7. Run the code, inspect the reconstruction preview and stored source image at final
   size, then record `code_path` and `reproduction_preview_path` in metadata. Only
   after this evidence exists may the agent call `ReferenceLibrary.review(...)`.
   Run `scripts/check_reference_reproductions.py`, `validate`, and rebuild the
   registry. A user-supplied reference without reproduction code remains `pending`
   and must not enter the reviewed recommendation pool.
8. Build an equal-size `reference-vs-reconstruction.png` comparison and inspect it
   in the order topology → marks/layers → data encoding → hierarchy/spacing →
   palette roles → annotations. Record every deviation in
   `assets/visual-references/review-evidence/reproduction-audit.json` and run
   `scripts/check_reference_reproduction_fidelity.py`. Do not call a reconstruction
   faithful merely because its script runs; a mismatched skeleton is a FIX.
   Optionally record equal-size SSIM/MAE evidence with
   `scripts/reference_image_analysis.py compare`; similarity supports but never
   replaces the six required structural judgments.
9. Report the reference ID, normalized type, tags, scope, review status, and exact
   relative image path. A stored reference is not automatically a production asset.

This route is intentionally one-image-at-a-time: each image receives its own visual
grammar and retrieval identity. Do not collapse a batch into one generic “nice figure”
record or reuse a previous palette/type merely because the files arrived together.

### Mandatory visual-optimization route

Requests to **optimize, polish, beautify, improve, redesign, or make an existing figure publication-quality** are major `revise` work unless the user explicitly limits the request to cosmetic edits. They always activate reference-led mode even when the user supplied no image:

1. Render and open the current figure; record structural, hierarchy, whitespace, density, legend, and legibility failures.
2. Run `scripts/reference_library.py recommend` with a required figure type and the current structural needs. It returns at most 3 candidates. Open every returned candidate's pixels and select one. For heterogeneous multi-panel figures, recommend separately for the assembly skeleton and each distinct panel family; do not apply one shortlist to every panel. Fewer than three candidates is valid; never fill the shortlist with another figure type. If none is compatible, use `build_new` and record why.
3. Complete the Reference Reconstruction Contract plus the Visual Optimization Contract in `references/reference-driven-reconstruction.md` before editing plotting code. The optimization record must state a fresh `palette_decision` and a `composition_decision` that explicitly rejects the old figure skeleton (hero evidence, support evidence, and what old equal-weight grid/legend structure is removed); old hex values may be retained only with an explicit semantic and contrast justification.
4. Make at least one evidenced structural or encoding change. Palette/font/alpha/line-width/marker-size/spacing-only changes are cosmetic and cannot satisfy an optimization request.
5. Render at final physical size, create an equal-cell `Before | Reference | After` comparison, inspect it, run `scripts/rendered_contrast.py` for every cell/tile annotation, and run `scripts/check_visual_optimization.py`. A FIX verdict blocks delivery. Passing source checks while retaining the old equal-weight subplot skeleton is a FIX, not a successful optimization.

The optimization checker is evidence-producing, not declaration-trusting: it recomputes contrast from the supplied after raster, verifies the after raster against declared physical dimensions/DPI, and rejects a comparison or contract whose evidence is stale. A helper merely defined in source is not compliance; it must be used and fixed light annotation colors are rejected.

When the selected reference comes from the bundled source archive, inspect its `reference_kind`: use a reviewed `exact_visual_source` as the visual sample, never an unreviewed `generated-archive` reconstruction. A source-specific reconstruction blueprint records what must be rebuilt; it does not certify that the redraw is visually faithful.

Do not force revise, review, export, or reference work through the full create route.

### Generated-archive lifecycle

The bundled generated archive is also a maintained reference corpus, not a pile of
unverified PNGs. After changing its renderer or dependencies, run
`scripts/audit_generated_reproductions.py --sync-previews` to execute every stored
`code.py`, refresh its `figure_card.json`, and require the fresh render to match the
stored preview. Then run
`scripts/make_generated_reproduction_contact_sheet.py` and inspect the actual pixels.
The audit records render success and stored-vs-fresh SSIM separately from source
fidelity: a deterministic redraw proves the code/preview contract, not that a
synthetic reconstruction is pixel-faithful to an unavailable source image.

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

Use a full contract for create/major revision, an abbreviated conclusion/evidence contract for a small revision, and no new contract for a user-explicit purely cosmetic edit. Never infer “cosmetic” from the existence of old plotting code. If the user provides data but no scientific question or requested chart, ask what the figure must show before designing it. For method/condition comparisons with paired points, operating points, or uncertainty, read `references/encoding-and-uncertainty.md` and classify the relationship before selecting a chart family.

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

Use `scripts/compose.py` for multi-panel assembly when compatible. Optional retrieval is allowed only for ordinary creation; strict recommendation is mandatory for visual optimization without a user-supplied reference. Use `scripts/reference_library.py recommend`, save its JSON report, and open every returned candidate's pixels. Do not use generic `query()` or a remembered global top three for optimization. User colors outrank user palettes; both outrank an optional library reference and defaults. A visual reference never changes scientific semantics. If a `reference_id` is supplied to style resolution, it must exist and its normalized `figure_type` must match the requested figure type; unknown or cross-type references are errors, never silent fallback to a default palette. Run `ReferenceLibrary.validate()` when maintaining the library; it validates metadata and that each referenced image still exists and matches its recorded `sha256`. For paired operating-point or multi-condition plots, do not default to a continuous-axis errorbar template: use the relationship classification, one-channel-per-variable mapping, and uncertainty hierarchy in `references/encoding-and-uncertainty.md`.

## Render and QA gate

Before delivery:

1. Run `scripts/qa_validator.py` on final plotting source and resolve every FAIL. For heatmaps, matrices, or colored tiles containing text, use `scripts/palette_manager.py` `pick_text_color()` for every annotation; fixed light text is not permitted.
2. Render only with the declared backend(s) and final assembler.
3. Run `scripts/audit_pdf_text.py <figure.pdf> --min-pt 5` on the vector master.
4. Inspect every panel and the assembled figure at final physical size using `references/checklist.md`. Measure every declared in-cell text region with `scripts/rendered_contrast.py`; normal text requires contrast ratio >= 4.5.
5. When reference-driven, create an equal-size reference/candidate comparison and run `scripts/check_reference_fidelity.py`. A FIX verdict blocks a claim of fidelity.
6. When visually optimizing, create an equal-cell before/reference/after comparison and run `scripts/check_visual_optimization.py`. A FIX verdict blocks delivery, even when source QA passes.
7. Run `scripts/check_skill_contract.py` only when maintaining this skill, not for each figure.

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
| Python plotting | `references/matplotlib.md`, `references/typography.md`, `references/color-palettes.md`; use `scripts/palette_manager.py` |
| R plotting | `references/r-rendering.md`; add `references/complexheatmap.md` only for ComplexHeatmap |
| Multi-panel assembly | `references/multipanel-layout.md` |
| Target journal | `references/journal-specs.md`, then `references/journal-intel.md` when journal-specific evidence is needed |
| Export/delivery | `references/export-specs.md`, `references/delivery-contract.md`, `references/figure-legend-contract.md` |
| QA/review | `references/checklist.md`, `references/common-pitfalls.md`; run `scripts/rendered_contrast.py` for in-cell text; add `references/revision-cases.md` for reviewer simulation |
| Optional reference library | `references/visual-reference-library.md`; use at most 3 reviewed/promoted candidates |
| Visual optimization | `references/reference-driven-reconstruction.md`, `references/visual-reference-library.md`; record a `palette_decision`, run `scripts/rendered_contrast.py`, then `scripts/check_visual_optimization.py` |
| Source reconstruction maintenance | `references/source-reconstruction-library.md`; run `scripts/audit_generated_reproductions.py --sync-previews --visual-inspected`, `scripts/make_generated_reproduction_contact_sheet.py`, `scripts/review_source_reconstructions.py`, `scripts/audit_source_reconstruction_batch.py`, `scripts/audit_source_catalog_batch.py`, `scripts/check_source_reconstruction_library.py`, and `scripts/check_source_reference_catalog.py` |

Do not import, execute, or copy an unlicensed third-party example collection. An audit may name such a collection and independently reconstruct its observable visual grammar with synthetic data and original code. Production assets under `assets/` remain implementation candidates and never override the adaptation gate.
