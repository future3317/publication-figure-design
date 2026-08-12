# Backend Selection

## Selection order

Choose the plotting backend in this order:

1. explicit user request;
2. workflow requirement, such as a required R-only package or an existing source the user asked to revise;
3. saved preference from `scripts/backend_preference.py get`;
4. Python default.

Save a preference only after an explicit user choice:

```bash
python scripts/backend_preference.py set python
python scripts/backend_preference.py set r
```

## Execution contract

A single-backend figure uses the selected backend for plotting, preview, vector/raster export, and visual-QA renders. If its runtime or a required package is missing, report the blocker and stop that render path. Do not silently generate a substitute in another language.

## Mixed mode

Mixed Python/R panels are allowed only when explicitly requested or a real panel capability requires them. Before rendering, declare:

| Panel | Backend | Required capability | Intermediate format |
|---|---|---|---|

Then name exactly one final assembler. The assembler may place rendered panels but must not redraw a selected-backend panel with another plotting backend. Use vector intermediates when feasible; if raster intermediates are necessary, render them at their final physical size and sufficient resolution.

If one panel runtime is missing, report that panel as blocked. Do not label a partial or cross-backend substitute as the completed figure.
