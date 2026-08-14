# Reference Candidate Selection Design

## Goal

Make visual-reference recommendations task-specific, explainable, structurally compatible, and diverse instead of repeatedly returning the same globally high-rated images.

## Ideal behavior

Visual optimization uses a dedicated recommender rather than the generic metadata query. The recommender requires a canonical figure type, admits only reviewed/promoted references of that type, applies required tags as hard constraints, and ranks task compatibility before aesthetic rating. Optional layout, density, group count, journal, and preferred tags affect compatibility scoring and are shown as matches or cautions.

The final set contains at most three candidates and greedily favors different subtypes, layouts, and source families when comparable alternatives exist. It never fills an empty slot with an unrelated figure. A result with fewer than the requested candidates is explicitly marked `insufficient_pool`.

Every run returns a machine-readable report containing the request, eligible-pool counts, candidate IDs and image paths, scores, match reasons, cautions, and diversity decisions. Codex must open every returned candidate image and make the final visual judgment from pixels; metadata scores only prepare the shortlist.

The generic `query()` API remains available for library administration and backward compatibility, but the skill forbids it as the candidate-selection path for visual optimization.

## Acceptance criteria

- Missing figure type is an error.
- Different figure types cannot receive the same unrelated shortlist.
- A tag/layout-compatible candidate outranks a marginally higher-rated mismatch.
- Required tags are hard filters.
- Candidate sets prefer subtype/layout/source diversity.
- Excluded IDs are not returned.
- Reports explain both matches and cautions.
- Candidate shortages are reported honestly.
