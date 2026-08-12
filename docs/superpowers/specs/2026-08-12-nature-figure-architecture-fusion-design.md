# Nature-Figure Architecture Fusion Design

Date: 2026-08-12

## Objective

Make `academic-figure-skill` obey a concrete reference image before it considers legacy plotting code, while reducing entrypoint context cost and adding deterministic checks for the fragile parts of the workflow.

## Source and licence boundary

The architecture review uses the Apache-2.0 repository `Yuan1z0825/nature-skills`, main-branch snapshot downloaded on 2026-08-12. The `nature-figure/assets/figures4papers` notice states that its upstream material has no explicit licence. Do not copy, modify, or redistribute anything from that directory. Adapt only general architecture and independently reimplement small Apache-licensed utilities when they fill a demonstrated gap.

## Diagnosed failure

The current entrypoint is 692 lines and mixes routing, contracts, tutorials, asset selection, code examples, QA, and delivery. Its reference gate is correct in isolation, but later `COPY-FIRST`, visual-adapt, and cross-type rules are large and salient. A model can therefore satisfy the early gate verbally and still retain an old visual skeleton, changing mainly colors or typography.

The fix is an ordering and information-architecture change, not another palette catalogue:

1. Put immutable precedence and blocking gates in a short always-loaded router.
2. Route detail through a declarative manifest and one-level references.
3. Replace overlapping reuse vocabularies with one four-level adaptation ladder.
4. Require observable evidence before legacy code can be selected.
5. Check the route and artifacts mechanically where possible.

## Capability and conflict matrix

| Source capability | Existing equivalent | Decision | Reason and proof |
|---|---|---|---|
| Short router plus manifest | 692-line hub, no root manifest | Adopt | Keeps hard gates salient; a contract test enforces router length, route links, and ordering. |
| Static core plus on-demand fragments | Always-load/on-demand table, but much detail remains inline | Adopt | Move asset workflow, backend policy, delivery, and QA detail into direct references. |
| Five-point figure contract including backend | Five points without backend | Adapt | Use conclusion, evidence, archetype, backend/assembler, journal/export. Keep review risk in QA instead of duplicating it. |
| Exact/structural/style/build-new taxonomy | `reuse/restructure/rewrite` plus COPY-FIRST/VISUAL ADAPT/PARAM INHERIT | Adapt | Use `exact_reuse`, `structural_adaptation`, `style_only`, `build_new`; map reference decisions deterministically and ban cosmetic reconstruction. |
| Explicit field mapping | Informal data-entry-point mapping | Adopt | Require source field, user field, semantic role, unit, allowed values, group/replicate/uncertainty definitions. |
| Persisted exclusive backend | Runtime detection and mixed Python/R composition | Adapt | Persist a default. A single-backend figure stays exclusive; mixed mode is allowed only when required and must name a final assembler. No silent substitution. |
| Source safety validator | Existing `qa_validator.py` | Selective merge | Add only demonstrated missing high-value checks; do not import a second 752-line validator. |
| PDF `Tf` glyph audit | Source fontsize checker only | Adopt | A dependency-free script catches mathtext/script glyphs below 5 pt after export. |
| Numerical layout helpers | Ad hoc plotting code | Adopt small helpers | Monotone interpolation and uncertainty-aware label placement prevent plausible-looking numerical/layout errors. |
| Figure legend contract | Scattered QA/statistics guidance | Adopt on demand | One concise contract covers title, panels, n/error/test, and source data. |
| Privacy boundary | Exact internal paths requested in reports | Adapt | Keep exact provenance in internal QA artifacts and source headers; sanitize normal user-facing summaries unless paths are requested. |
| `agents/openai.yaml` | Missing | Adopt | Align UI metadata with the actual skill. |
| OpenRouter schematic route | Outside raster/chart scope | Reject | Image generation is already handled by the image-generation skill. |
| `figures4papers` assets/scripts | Similar local asset library | Reject | Upstream notice gives no redistribution licence. |
| Whole validator/gallery import | Existing validators and assets | Reject | Duplicates present functionality and increases maintenance/context cost. |

## Target architecture

### Entrypoint

Keep `SKILL.md` below 300 lines. It contains only:

- mode dispatch;
- the evidence-first precedence rule;
- the core workflow and stop conditions;
- the reference gate and adaptation ladder;
- the backend/assembler gate;
- the data-integrity boundary;
- the render/QA/delivery gate;
- a declarative resource routing table.

Do not duplicate detailed checklists or implementation recipes in the entrypoint.

### Manifest

Add root `manifest.yaml` as the routing source of truth. It declares:

- always-loaded core references;
- conditional routes and their required references/scripts;
- backend selection policy;
- validation commands.

The manifest guides the agent; `SKILL.md` remains authoritative if prose and manifest conflict. A checker prevents drift between them.

### Unified adaptation ladder

Use one ladder for bundled assets, archived examples, and user references:

1. `exact_reuse`: all five structural dimensions match; change only data mapping and declared parameters.
2. `structural_adaptation`: scientific encoding/chart family matches, but layout, layers, geometry, or legend model must change.
3. `style_only`: structure or dimensionality differs; inherit only compatible palette roles, typography, spacing, or annotation treatment.
4. `build_new`: no compatible structural or stylistic source.

For a concrete reference, map the existing fidelity vocabulary as follows:

- `reuse` -> `exact_reuse`
- `restructure` -> `structural_adaptation`
- `rewrite` -> `style_only` or `build_new`, depending on whether compatible style tokens remain

Reference structure still outranks production code. `exact_reuse` is forbidden until panel topology, mark geometry, layer topology, data encoding, and annotation/legend model are all evidenced.

### Backend policy

Resolve backend in this order:

1. explicit request;
2. workflow requirement;
3. saved preference;
4. current skill default (`python`).

Save only an explicit user choice. A normal figure has one plotting backend. Mixed mode requires a real panel capability need or explicit user request, a declared backend per panel, and one declared final assembler. If a selected runtime/package is missing, stop that render path and report the blocker; never silently substitute another backend.

### QA

The lightweight gate has three layers:

1. `check_skill_contract.py`: validates skill architecture, route targets, gate order, taxonomy, manifest, metadata, and restricted third-party path references.
2. Existing source QA plus two small safety additions: numerical helpers and real PDF glyph-size audit.
3. Existing rendered visual inspection and reference-fidelity checker.

The checker is intentionally not a semantic image-similarity model. Reference fidelity remains an observable contract plus equal-size visual inspection, because different truthful data cannot be judged by pixel similarity.

## Compatibility decisions

- Preserve the public `ReferenceLibrary`, palette manager, production assets, compose engine, and current RF-1..RF-10 contract.
- Preserve mixed Python/R composition as an explicit exception, not the default.
- Keep old reports and install adapters as history/compatibility artifacts; do not load them during normal skill use.
- Update tests that assert wording from the oversized hub to assert behavior and routes instead.

## Test strategy

RED tests must show the current skill lacks:

- a short declarative router and root manifest;
- unified adaptation terms and five-dimension exact-reuse gate;
- backend persistence with explicit mixed-mode exception;
- PDF glyph audit and numerical helpers;
- legend/privacy contracts and UI metadata;
- a self-check that detects route drift and prohibited third-party imports.

GREEN implementation adds the smallest direct files and edits needed. Regression then runs all existing unit/integration suites, reference integrity, QA coverage, e2e smoke, skill quick validation, and the new self-check.

## Self-review

- The design strengthens the user's concrete complaint rather than merely adding palettes.
- It does not import licence-unclear material.
- It does not remove a working mixed-backend capability.
- It creates one taxonomy instead of adding a fourth overlapping vocabulary.
- Deterministic checks cover structure and evidence; subjective visual judgment stays explicitly manual/rendered.
- The additional scripts are small, dependency-free except the numerical helper's existing NumPy expectation, and have direct tests.
