# Production Asset Metadata

> Agent-facing guide for `assets/figures/<type>/metadata.json` sidecars.
> For the API, see `scripts/production_asset_manager.py`.

## Purpose

Help the agent decide, **before reading the full script**, whether a production asset is:

- a **template** it can safely COPY-FIRST and adapt to user data, or
- an **example** whose visual system is valuable but whose data is hard-coded, or
- a **reusable** component somewhere in between.

This makes Step 4 (Production Asset Scan) faster and reduces bad native-run attempts.

## File location

One sidecar per production asset directory:

```
assets/figures/<figure-type>/metadata.json
```

It describes the canonical script(s) in that directory. If multiple scripts exist, use `variant` to distinguish them.

## Schema

```json
{
  "id": "groupedviolin_plot_groupedviolin",
  "figure_type": "GroupedViolin",
  "variant": "default",
  "asset_kind": "template",
  "runtime": "python",
  "dependencies": ["numpy", "pandas", "matplotlib", "scipy"],
  "data_shape": "wide",
  "grouping": "multi-group columns",
  "preview": "plot_GroupedViolin.png",
  "palette_policy": "adaptable",
  "production_ready": true,
  "notes": "Reusable function plot_violin_significance; expects wide DataFrame with one column per group."
}
```

### Field reference

| Field | Required | Allowed values | Meaning |
|---|---|---|---|
| `id` | yes | string | Stable identifier. Use `<figure_type>_<script_stem>` convention. |
| `figure_type` | yes | string | Matches the directory name in `assets/figures/` and `references/directory-map.md`. |
| `variant` | no | string | Distinguishes multiple scripts of the same figure type. Default `"default"`. |
| `asset_kind` | yes | `template`, `reusable`, `example` | Reuse recommendation (see below). |
| `runtime` | yes | `python`, `r`, `mixed` | Language runtime needed. |
| `dependencies` | no | list of strings | Top-level packages the script imports. |
| `data_shape` | no | `wide`, `long`, `matrix`, `xy`, `paired`, ... | Expected data layout. |
| `grouping` | no | string | How groups/categories are represented. |
| `preview` | no | filename | Canonical preview image inside the same directory. |
| `palette_policy` | no | `preserve`, `adaptable` | Whether the asset's palette should be kept or may be adjusted. |
| `production_ready` | yes | boolean | `false` means do not COPY-FIRST without strong reason. |
| `notes` | no | string | One-sentence guidance for the agent. |

### `asset_kind` semantics

- **`template`** — Contains a reusable function with clear data entry points. Safe for VISUAL ADAPT (column mapping) and often safe for native run after path replacement.
- **`reusable`** — Has reusable logic but needs more careful inspection; may mix demo data with function code.
- **`example`** — Heavily tied to a specific dataset or paper. Do not naive-run on unrelated data. Use for PARAM INHERIT or cross-type inheritance instead.

## How Step 4 uses metadata

After matching a figure type via `references/directory-map.md`:

1. Check for `assets/figures/<type>/metadata.json`.
2. If it exists, read it **first**.
3. Apply this decision shortcut:

```
asset_kind = template AND production_ready = true
    → strong COPY-FIRST candidate; inspect data entry points, then native run.

asset_kind = reusable
    → inspect data entry points; COPY-FIRST only if structure matches clearly.

asset_kind = example OR production_ready = false
    → do NOT native-run on unrelated data.
      Use VISUAL ADAPT / PARAM INHERIT / cross-type inheritance instead.

metadata.json missing
    → fall back to current behavior: read script, identify data entry points.
```

The agent still opens the preview PNG and verifies the script, but the metadata prevents obviously wrong choices.

## Promotion from Visual Reference

A visual reference can become a production asset after review:

1. User archives a generated figure with `archive_generated_figure(...)`.
2. User reviews it and sets `review_status="reviewed"` and `production_ready=true`.
3. Call `ProductionAssetLibrary.promote_from_visual_reference(ref_id, ...)`.
4. The manager copies the archived code + image into `assets/figures/<figure_type>/`, writes `metadata.json`, and leaves the original reference unchanged.

Only `reviewed` + `production_ready` references can be promoted. The original reference stays in `assets/visual-references/` for provenance.
