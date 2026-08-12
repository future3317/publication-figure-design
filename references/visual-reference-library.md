# Visual Reference Library

> On-demand reference for agents using `assets/visual-references/` during figure creation.
> For full API and CLI details, see `scripts/reference_library.py`.

## Two reference workflows

If the user supplies, points to, selects, or asks to match a **concrete reference image**, use `references/reference-driven-reconstruction.md`. That workflow is mandatory, and the concrete reference outranks production code after scientific integrity and explicit user requirements.

The retrieval workflow below is for **optional style discovery** when no concrete reference has been selected.

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

Default retrieval limit is **3 references** per create task. Do not load more metadata or images than necessary.

If no reference matches, continue the normal workflow.

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
