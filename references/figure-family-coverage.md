# Scientific Figure-Family Coverage

Use this guide before choosing a chart. A paper figure is selected by the
evidence relationship and the reader's comparison task, not by the name of a
familiar plotting function. The executable taxonomy and reference-library audit
live in `scripts/figure_family_coverage.py`.

## Decision order

1. State the claim and the evidence job of each panel.
2. Classify the relationship: independent categories, paired observations,
   continuous/time, distribution, threshold classification, spatial/image,
   relational network, or mechanism/architecture.
3. Choose the smallest family whose visual channels express that relationship.
4. Choose a subtype and record the family in the figure contract.
5. Query the reference library for that exact family/subtype. If coverage is
   missing, record `build_new`; do not substitute a nearby family silently.

The family choice does not override scientific semantics. In particular, a few
method-specific operating points are categorical/paired even when their labels
are numbers, and an embedding axis is not a calibrated scientific measurement
unless the analysis defines it that way.

## Family map

| Family | Use for | Prefer | Avoid |
|---|---|---|---|
| `comparison_effect` | Independent groups, effect estimates, distributions by condition | Raw points plus interval/violin/box/raincloud; forest intervals for many estimates | Mean-only bars that hide n and spread; decorative dual axes |
| `distribution_uncertainty` | Shape, tails, quantiles, or time-to-event distributions | ECDF, density/ridge, histogram, survival/KM with censoring marks | Comparing densities with incompatible bandwidths or bin widths |
| `trend_trajectory` | Ordered time, training, dose, or repeated trajectory | Lines with explicit sampling, uncertainty ribbons, and direct labels | Connecting unordered categories; smoothing away observed endpoints |
| `paired_operating_point` | Before/after, matched seeds, method pairs, operating points | Dumbbells, slopegraphs, connected paired points, aligned small multiples | Independent bars or a continuous line implying unsupported intermediate states |
| `classification_diagnostics` | Ranking, probability quality, and threshold decisions | Separate ROC/PR, calibration, confusion/decision curves with prevalence and threshold context | Treating ROC AUC as calibration; hiding class imbalance |
| `relationship_embedding` | Associations, regressions, PCA/UMAP/t-SNE/manifolds | Scatter with density/labels and declared embedding meaning | 3D perspective when 2D is sufficient; causal language from correlation |
| `matrix_array` | Correlation, confusion, expression, similarity, or adjacency matrices | Masked/diverging heatmaps, clustered matrices, readable cell annotations | Unstated normalization/midpoint; light text on light cells; arbitrary clustering |
| `network_flow_set` | Graphs, pathways, flow conservation, membership sets | Stable node layout, weighted/directed edges, Sankey/alluvial, UpSet | Edge crossings as an encoding; Sankey widths without conservation units |
| `spatial_image` | Microscopy, anatomy, maps, segmentation, spatial fields, in-vivo images | Image + quantitative companion, scale/orientation, explicit overlays | Cropping without field-of-view; intensity changes without disclosure |
| `mechanism_architecture` | Model, pipeline, material, causal or conceptual explanation | Hero schematic plus supporting evidence, semantic arrows, explicit layer order | Mixing measured vectors and explanatory arrows; unlabeled decorative 3D |
| `statistical_discovery` | Genome-wide/discovery thresholds and effect-size screening | Volcano/MA/Manhattan, enrichment, forest/funnel with threshold and multiplicity context | Labeling only “interesting” points; hiding the tested population |
| `optimization_sensitivity` | Ablation, robustness, scaling, Pareto/resource trade-offs | One controlled change per ablation, log-log scaling, Pareto dominance, seed intervals | Changing multiple factors in one bar; claiming robustness without perturbation coverage |

The full aliases, selection rules, and required observations for these families
are in the executable taxonomy. A family card should include:

```json
{
  "figure_family": {
    "id": "paired_operating_point",
    "subtype": "dumbbell",
    "evidence_intent": "matched improvement at three operating points",
    "data_relationship": "paired",
    "required_channels": ["x=operating point", "y=metric", "line=pair identity"],
    "non_negotiable_rules": ["do not imply a continuous path between states"]
  }
}
```

This family card complements the visual-grammar card. The family card says what
the figure must mean; the visual-grammar card says how the selected reference
draws it. For example, a `mechanism_architecture` card can require semantic
arrows and a hero object, while the visual grammar records that the arrows are
muted red, gently curved, thin, edge-anchored, and behind the labels.

## Family-specific review traps

- **Comparisons:** check the zero/reference line, replicate visibility, interval
  definition, category order, and whether a bar's area is misleading.
- **Trends:** check x ordering, sampling cadence, missing values, smoothing,
  confidence-band overlap, and whether the same series keeps its style in every
  panel.
- **Pairs/operating points:** check pair identity and direction; use direct
  labels or a local key when panel membership differs.
- **Classification:** check prevalence, threshold markers, calibration bins,
  confidence bands, and the difference between ranking and probability quality.
- **Matrices:** check row/column ordering, midpoint, normalization, missing
  values, annotation contrast, and colorbar scope.
- **Networks/flows:** check node/edge roles, direction, edge width units,
  layout stability, crossings, and label collision handling.
- **Images/spatial:** check scale bar, orientation, crop, registration, dynamic
  range, segmentation semantics, and the link from image to quantification.
- **Mechanisms:** check object material/depth, semantic versus measured arrows,
  stage grouping, occlusion, and legend/direct-label scope.
- **Discovery/optimization:** check threshold/multiplicity context, control,
  changed component, resource axis, seed uncertainty, and whether all tested
  cases remain visible.

## Reference-library audit

Run this before declaring the library broad enough for a new paper:

```bash
python scripts/figure_family_coverage.py
```

The audit reports reviewed candidate IDs per family and explicit gaps. In the
current installed library it finds 10 of 12 families represented; the missing
families are `paired_operating_point` and `classification_diagnostics`. Those
are actionable acquisition targets, not reasons to reuse a generic bar chart.

For a new figure, use the exact family and subtype as retrieval filters, open
every returned image, and record which candidate controls the assembly or panel.
A reference from another family may supply compatible visual tokens only after
the adaptation level is declared; it cannot silently redefine the chart family.
