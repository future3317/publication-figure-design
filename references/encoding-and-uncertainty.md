# Encoding and Uncertainty Decisions

Use this guide when a figure compares methods, conditions, operating points, or before/after values—especially when points have error bars and a connecting line. The aim is to make the scientific relationship readable before styling details are chosen.

## First classify the relationship

Decide which relationship the data actually support:

Use the **paired comparison** test before choosing a connected plot: the same method or sample must have a meaningful identity across conditions. A numeric x axis alone does not establish a **continuous relationship**.

| Data relationship | Default visual grammar | Do not imply |
|---|---|---|
| **Paired comparison**: the same method/sample has two or more linked conditions | paired dot plot, dumbbell plot, slopegraph, or small multiples with aligned rows | a continuous trend between only two observed states |
| **Continuous relationship**: many ordered x values and a meaningful trajectory | line/scatter with a restrained uncertainty band | a categorical before/after comparison |
| **Independent groups**: groups are not linked observations | grouped dot/box/violin/forest plot | a connecting segment that suggests pairing |
| **Operating points**: a small set of explicitly chosen configurations | categorical method/condition layout, or a compact two-axis operating-point panel | a smooth optimization path unless intermediate states are observed |

If x positions are only method-specific locations, do not use a wide continuous x-axis merely because the variable is numeric. Use method as the categorical organizing axis and label the numeric state beside the mark, or use a dedicated operating-point panel.

## One job per visual channel

Before coding, write a mapping table for position, color, shape/fill, line, size, and uncertainty. A variable gets one primary visual channel; a secondary cue is allowed only to preserve accessibility or pairing.

- **Position** carries the quantitative comparison whenever possible.
- **Color** identifies method/group or one semantic emphasis, not several unrelated conditions.
- **Shape/fill** identifies a small condition set such as cap, replicate state, or observed/predicted.
- **Connecting lines** mean a real pairing or ordered path; they are not decoration.
- **Size** is reserved for a meaningful third quantitative variable and should not compete with uncertainty.
- **Error bars/bands** show uncertainty only. State whether they are SD, SEM, CI, seed variation, or another interval.

Do not let a single line simultaneously read as an uncertainty interval, a condition transition, and a trend. If those roles coexist, separate their layers visually: thin/desaturated connector, subdued uncertainty, prominent point; or use a band/ellipse and remove the connector.

## Paired operating-point figures

For two conditions per method (for example, two caps, budgets, or deployment states):

1. Keep the method order shared across panels.
2. Prefer categorical rows/columns or aligned small multiples when numeric x positions create large empty gaps.
3. Connect only paired centers; draw the connector behind the points and lighter than the points.
4. Keep horizontal and vertical uncertainty visually subordinate (thin line, short cap, or a translucent interval). If both dimensions matter, consider a confidence ellipse or separate marginal uncertainty rather than oversized crosshair error bars.
5. Encode the condition once. A filled/open marker plus a second legend sentence is usually redundant; use one combined legend or direct labels.
6. Label numeric operating states next to the points when the value itself matters. Do not force the reader to infer them from a distant continuous axis.
7. If accuracy and compute are separate outcomes, use coordinated panels with shared method/condition order, not two independently positioned x-axis stories.

## Hierarchy and finishing

- Establish a focal question and give one panel or one comparison the visual priority; supporting metrics should be quieter.
- Use one legend model for the whole figure. Merge method and condition entries when jointly decoded, or direct-label the few points.
- Avoid oversized titles that repeat the axis meaning. Use concise panel labels and a short descriptive subtitle only when needed.
- Remove heavy gridlines and four-sided axes; preserve enough reference structure to read values.
- Check the figure at final physical size and as a thumbnail. At thumbnail size, the reader should still see the method order, paired relationship, and main conclusion—not a forest of caps and crossing lines.

## Design review questions

Before accepting a render, answer:

1. Is this paired, continuous, or independent data?
2. What is the primary comparison the reader should make in three seconds?
3. Which variable owns each visual channel, and is any channel overloaded?
4. Does every connector represent a real pairing or observed sequence?
5. Are uncertainty marks weaker than the estimates and distinguishable from connectors?
6. Would a categorical layout, aligned rows, or small multiples make the comparison clearer than a continuous axis?
7. Is the legend complete in one place, and are condition labels readable at final size?

If any answer is unclear, redesign the composition before changing colors or fonts. A palette adjustment cannot repair an overloaded encoding grammar.
