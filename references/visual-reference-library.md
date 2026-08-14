# Visual Reference Library

> On-demand reference for agents using `assets/visual-references/` during figure creation.
> For full API and CLI details, see `scripts/reference_library.py`.

## Direct image intake (the normal user-facing entry point)

When a user supplies a single image to save, the agent can complete the intake without
source code or raw data. Follow this exact contract:

| Field | Required decision |
|---|---|
| Pixels | Open and inspect the image itself; never classify from a filename or thumbnail |
| Figure type | Normalize the dominant family (`learning_curves`, `scatter_marginal`, `architecture_schematic`, etc.); use `mixed_multi_panel` when no dominant family is honest |
| Visual grammar | Record topology, hero/support hierarchy, mark/encoding channels, layout, density, annotation/legend model, background, and palette roles |
| Provenance | Default to `license="user-supplied; redistribution not established"` and `usage_scope="private_reference"` |
| Reproduction | Add runnable reference-local code using synthetic/example data and render a `reconstruction.png` preview; original data/code is not required |
| Fidelity review | Build an equal-size `reference-vs-reconstruction.png` pair, inspect the six visual-grammar dimensions, and record explicit deviations in the reproduction audit |
| State | Ingest as `review_status=pending`, then review only after final-size inspection |
| Output | Sidecar metadata (`code_path`, `reproduction_preview_path`) + copied image + reconstruction preview + rebuilt `assets/registry.jsonl`; never hand-edit the registry |

The minimal command is:

```bash
python scripts/reference_library.py ingest \
  path/to/reference.png learning_curves \
  --metadata '{"source":"user-supplied reference image","license":"user-supplied; redistribution not established","usage_scope":"private_reference","reference_kind":"user_supplied","tags":["multi-panel","uncertainty-ribbon","training-dynamics"],"layout":"2x2","data_density":"moderate","notes":"Inspect stored pixels before applying; visual inspiration only."}'
python scripts/reference_library.py validate
python scripts/reference_library.py rebuild
python scripts/check_reference_reproductions.py
python scripts/check_reference_reproduction_fidelity.py
```

The agent must return the assigned reference ID and relative image path. If the user
later supplies a clear redistribution license, update the provenance metadata through
the normal review/maintenance path; do not silently promote an unlicensed image into a
public bundle or a runnable production asset.

For a batch, run the same intake independently for every image. Each record must have
its own type, tags, and visual-grammar notes; a batch is not permission to assign the
same three candidates to every future task.

## Two reference workflows

If the user supplies, points to, selects, or asks to match a **concrete reference image**, use `references/reference-driven-reconstruction.md`. That workflow is mandatory, and the concrete reference outranks production code after scientific integrity and explicit user requirements.

The retrieval workflow below supports **optional style discovery** for ordinary creation, but is mandatory for visual optimization when no concrete reference has been selected.

## When to use optional retrieval

In **create** mode, after the figure type is known and before finalizing the visual plan, query the library for inspiration on:

- palette choice and palette policy
- layout (1x1, 2x2, hero-panel, etc.)
- annotation style
- legend position
- data density / spacing
- highlight strategy

Do NOT use visual references to override scientific semantics or to force an incompatible figure type.

## Responsibility split

| Production Asset (`assets/figures/`) | Visual Reference (`assets/visual-references/`) |
|---|---|
| Correct implementation of this figure type | Visual language inspiration for this figure type |
| Data structure, geometry, statistics | Palette, layout, annotation, density, spacing, legend, highlight |
| Must run with user data | Does NOT need to run; informs design decisions |

## Querying

Use the Python API from `scripts/reference_library.py`:

```python
from scripts.reference_library import ReferenceLibrary

refs = ReferenceLibrary().query(
    figure_type="GroupedViolin",
    tags=["pastel", "minimal"],
    journal_style="Nature",
    min_aesthetic_rating=3,
    limit=3,
)
```

Default retrieval limit is **3 references** per task. Normal queries return only `reviewed` or `promoted` entries; `pending` and `rejected` are quarantined unless maintenance code explicitly passes `include_unreviewed=True`. Open the pixels of every returned candidate considered for use. Metadata and contact sheets alone do not count as inspection.

`reference_kind=exact_visual_source` means a separately cataloged original visual sample. It may be retrieved only after direct pixel review; a `generated-archive` independent reconstruction may be retrieved only after a passing source-to-render comparison. Never treat a matching family label, a successful render, or a source-specific blueprint as visual approval.

For ordinary creation, if no reference matches, continue the normal workflow. For visual optimization, record the attempted taxonomy/tags and use `build_new`; do not fall back to an unreviewed reconstruction.

Figure types are normalized on ingest and query. Common spellings such as `GroupedBar`, `grouped-bar`, and `bar_grouped` map to `grouped_bar`; `Heatmap` maps to `heatmap_grid`; `Scatter` maps to `scatter_bubble`.

Style resolution is type-safe: a supplied `reference_id` must resolve to an existing reference whose normalized figure type matches the requested production figure type. Unknown IDs and cross-type IDs raise an error; they are not replaced with the default palette or treated as generic inspiration. This prevents a style lookup from silently changing the chart family.

## Review-state integrity

Automated ingest and reconstruction always produce `review_status=pending`, `aesthetic_rating=null`, and `production_ready=false`. For `reference_kind=user_supplied`, review additionally requires runnable `code_path`, an existing `reproduction_preview_path`, and an inspected equal-size reference/reconstruction comparison with explicit deviations; a pasted image or runnable script alone is not a complete reviewed reference. Only an explicit rendered visual review may set an aesthetic rating and change status to `reviewed`. Only an explicit implementation audit may use `promoted`. Never use generation success, source-code checks, registry integrity, or the creator's self-report as aesthetic approval.

Record a completed review through `ReferenceLibrary.review(reference_id, rating, visual_review)`. The evidence object must set `final_size_inspected=true`, provide `pass` or `justified_deviation` for hierarchy, panel balance, whitespace, legend footprint, and text legibility, and name the reviewer/review pass. `ingest()` and `archive_generated_figure()` deliberately ignore self-approval fields in metadata overrides.

`ReferenceLibrary.validate()` also checks the referenced image file. A missing or unreadable image, a missing `sha256`, or pixels whose digest differs from metadata makes validation fail; repair the asset or metadata before using the reference.

## Applying a retrieved inspiration reference

Priority order (highest first):

1. Scientific semantics and user data structure
2. User explicit requirements
3. Production asset implementation
4. Retrieved inspiration reference
5. Skill default visual baseline

This order does not apply to a concrete user-selected reference. Use the reference-driven precedence in `references/reference-driven-reconstruction.md` for that case.

Palette priority (highest first):

1. User explicit colors
2. User explicit palette
3. Production / reference original palette
4. Skill default palette

If a reference has `palette_policy = preserve`, keep its palette logic unless the user overrides it.  
If `palette_policy = adaptable`, you may adjust through `palette_manager` or user preference.

## Recording visual sources

In the final QA/delivery report, record:

```
Production asset: GroupedViolin/plot_GroupedViolin.py
Visual reference: vr_44933a30fd0c3c58
Palette: summer_beach
Palette policy: preserve
```

If no visual reference was used, write `Visual reference: None`.

## Reference task shortcuts

Natural-language intents map to existing API:

| User says | Maps to |
|---|---|
| "把这张图存起来" / "这张我喜欢，收进参考库" | `ReferenceLibrary().ingest(...)` for external images; `archive_generated_figure(...)` for skill-generated images |
| "找几个好看的 grouped violin" | `query(figure_type="GroupedViolin", ...)` |
| "有没有 pastel 风格的 PCA 参考" | `query(figure_type="PCA", tags=["pastel"], ...)` |
| "找 Nature 风格、4 组、简洁的小提琴图" | `query(figure_type="Violin", tags=["Nature", "minimal"], n_groups=4, ...)` |

Do not build a second reference system; reuse `ReferenceLibrary`.

## Strict recommendation for visual optimization

Do not use `query()` to choose optimization candidates. Run:

```bash
python scripts/reference_library.py recommend \
  --figure-type Heatmap \
  --required-tags correlation \
  --preferred-tags annotation,direct-labels \
  --layout 2x2 --data-density high --limit 3 \
  --json candidate-recommendation.json
```

`figure-type` is mandatory and exact after alias normalization. Required tags are hard filters. Layout, density, group count, journal style, and preferred tags rank task compatibility before aesthetic rating. The final shortlist favors distinct subtypes, layouts, and source families among otherwise useful candidates.

The report contains pool counts, match reasons, cautions, diversity reasons, image paths, and scores. `insufficient_pool` is an honest result: open the one or two compatible candidates returned, or use `build_new` when none exist. Never substitute unrelated figure types merely to reach three candidates.

For a heterogeneous multi-panel figure, make separate recommendation requests for the overall assembly archetype and for each distinct panel family that needs its own visual grammar. A heatmap candidate may guide the heatmap panel, while a line-trend candidate guides the trend panel; neither becomes a universal template for the whole figure. Record which candidate controls which panel or assembly role.

After opening the pixels, record one concrete observation per candidate and explain the final selection in structural terms. “Highest score” or “looks best” alone is not a valid selection reason.
