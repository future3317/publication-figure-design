# Create Workflow

Use this route for a new manuscript figure or a major structural revision.

## 1. Establish the contract

Read `figure-contract.md`. State the core claim, evidence chain, archetype, backend/final assembler, and journal/export target. Do not create filler panels. If the scientific question is missing and the user did not specify a chart, obtain it before designing.

## 2. Inspect the data for the stated question

Record shape, field types, identifiers, groups, replicate unit, missingness, units, and plausible domains. Compute only summaries needed to choose truthful encodings. Preserve all observations unless the user authorizes an explicit scientific subset.

## 3. Resolve visual evidence before code

If a concrete reference exists, complete `reference-driven-reconstruction.md` before opening a production script. Otherwise, optional reference-library retrieval may return at most three candidates; inspect any candidate actually used.

## 4. Resolve backend and implementation

Follow `backend-selection.md`. Then follow `asset-adaptation.md` to map fields and select `exact_reuse`, `structural_adaptation`, `style_only`, or `build_new`. Do not choose implementation material by filename similarity alone.

## 5. Build at final size

Load the relevant plotting backend reference, typography, palette, journal dimensions, and export settings. Define semantic color roles before hex values. Build every panel around its unique evidence job. Remove redundant legends, decoration, and repeated encodings.

## 6. Validate data before rendering

Assert transform domains, finite values, group order, uncertainty semantics, and exclusion counts. Remove or isolate every simulated-data path. Use render-aware strategies instead of sampling for performance.

## 7. Render and inspect

Render with the declared backend(s). Inspect each panel and the assembly at final physical size. Check clipping, occlusion, typography, hierarchy, uncertainty coverage, legend placement, and color roles. Fix and rerender; do not approve from source alone.

## 8. Validate and deliver

Run source QA, PDF glyph audit, and the reference-fidelity gate when active. Follow `delivery-contract.md`. Report limitations honestly when a runtime or rendered check is unavailable.
