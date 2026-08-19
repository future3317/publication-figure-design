# Create Workflow

Use this route for a new manuscript figure or a major structural revision.

## 1. Establish the contract

Read `figure-contract.md`. State the core claim, evidence chain, archetype, backend/final assembler, and journal/export target. Do not create filler panels. If the scientific question is missing and the user did not specify a chart, obtain it before designing.

## 2. Inspect the data for the stated question

Record shape, field types, identifiers, groups, replicate unit, missingness, units, and plausible domains. Compute only summaries needed to choose truthful encodings. Preserve all observations unless the user authorizes an explicit scientific subset.

## 3. Resolve visual evidence before code

If a concrete reference exists, complete `reference-driven-reconstruction.md` before opening a production script. For an ordinary new figure, optional reference-library retrieval may return at most three reviewed/promoted candidates. For visual optimization without a supplied reference, open the current render and run the strict `recommend` route with a required figure type, structural needs, and preferred visual features. Save the JSON report, open every returned candidate's pixels, and record a candidate-specific observation. Select one or document why `build_new` is necessary. Never use generic `query()` or cross-type filler for this step.

## 4. Resolve backend and implementation

Follow `backend-selection.md`. Then follow `asset-adaptation.md` to map fields and select `exact_reuse`, `structural_adaptation`, `style_only`, or `build_new`. Do not choose implementation material by filename similarity alone.

For comparisons with multiple conditions, operating points, paired observations, or uncertainty, read `encoding-and-uncertainty.md` before choosing the chart family. Classify the relationship as paired, continuous, independent, or operating-point; write the visual-channel mapping; and reject a continuous-axis errorbar template when x positions are only method-specific locations.

## 5. Build at final size

Load the relevant plotting backend reference, typography, palette, journal dimensions, and export settings. Define semantic color roles before hex values and select colors with `scripts/palette_manager.py`, rather than inheriting hard-coded colors from prior scripts. Build every panel around its unique evidence job. Remove redundant legends, decoration, and repeated encodings. For any text on a filled heatmap/matrix/tile, call `pick_text_color(cell_color)`; never use a fixed white/light label. When paired points have connectors and uncertainty, draw the connector behind the points and subordinate both connector and uncertainty to the estimates; use one combined legend or direct labels for the condition.

## 6. Validate data before rendering

Assert transform domains, finite values, group order, uncertainty semantics, and exclusion counts. Remove or isolate every simulated-data path. Use render-aware strategies instead of sampling for performance.

## 7. Render and inspect

Render with the declared backend(s). Inspect each panel and the assembly at final physical size. Check clipping, occlusion, typography, hierarchy, uncertainty coverage, legend placement, and color roles. For paired/operating-point figures, inspect whether the categorical or continuous axis implies the intended relationship, whether connectors are genuine pairings, and whether error bars overpower the point estimates. Inspect at final physical size and as a thumbnail. For every declared text-on-fill region, run `scripts/rendered_contrast.py` and require >=4.5:1 contrast. Fix and rerender; do not approve from source alone.

## 8. Validate and deliver

Run source QA, PDF glyph audit, and the reference-fidelity gate when active. For visual optimization, also build the equal-cell `Before | Reference | After` comparison and run `scripts/check_visual_optimization.py`; FIX blocks delivery. Follow `delivery-contract.md`. A missing render/runtime is a blocker for a visual-optimization completion claim, not a skippable warning.
