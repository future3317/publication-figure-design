# Scientific Figure Design Compiler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 reference-first publication figure skill 收敛为可解析、可检索、可编译、可修补、可分层验收的 Scientific Figure Design Compiler，并清理失效旧入口。

**Architecture:** 保留现有 `Route → Intake → Reference Retrieval → Reference Inspection → Design Spec → Binding → Render → Compare → Critique → Repair → QA → Export` 状态机。新增 ReferenceDNA/StyleCapsule/DesignPacket/DesignPatch/RenderTrace 等当前单一数据合同；把参考分析、检索、风格编译、布局、修补、QA 作为 `src/publication_figure_design` 的核心，`scripts/` 只保留薄 CLI 和维护命令。

**Tech Stack:** Python 3.11 (`D:\Anaconda\envs\piepaper\python.exe`), dataclasses/JSON/YAML, NumPy/Pillow/Matplotlib；可选 PyMuPDF、colorspacious、kiwisolver、scikit-learn、svgutils/CairoSVG、LPIPS/DreamSim、SigLIP/DINO 通过 extras 使用，不把重模型装进 core。

**Spec:** `E:\Downloads\升级意见.md`

## Global Constraints

- 所有科研绘图、参考分析、QA、benchmark 和生命周期命令使用 `piepaper` 的显式 `python.exe`。
- 保留现有 12 阶段状态机，不创建第二条生产工作流。
- 参考源按 raster/SVG/PDF/code 分析；raster 不猜精确字体，只输出字体类别和相对层级。
- ScientificContract 优先于视觉参考；参考只决定视觉语法。
- 正式推荐仍遵守 `raw → analyzed → reviewed → benchmarked → production` quarantine。
- 核心逻辑进入 `src/`；旧的 `sys.path` 注入和重复实现清理掉。
- 测试、benchmark、CI 只在全部实现和旧路径清理完成后统一执行。
- 不创建 `v1/v2/final` 普通副本；schema 的正式版本字段仅用于持久化合同兼容。

---

### Task 1: 扩展统一合同与 Reference DNA

**Files:**
- Modify: `src/publication_figure_design/contracts/models.py`
- Modify: `src/publication_figure_design/contracts/__init__.py`
- Modify: `schemas/contracts.schema.json`
- Create: `src/publication_figure_design/reference_intelligence/dna.py`
- Create: `src/publication_figure_design/reference_intelligence/__init__.py`

**Interfaces:**
- `ReferenceDNA.from_metadata(metadata: Mapping[str, Any]) -> ReferenceDNA`
- `ReferenceDNA.to_dict() -> dict[str, Any]`
- `ReferenceDNA.validate() -> list[str]`
- `StyleCapsule.to_dict() -> dict[str, Any]`
- `DesignPacket.to_dict() -> dict[str, Any]`
- `DesignPatch.apply(packet: Mapping[str, Any]) -> dict[str, Any]`
- `RenderTrace.to_dict() -> dict[str, Any]`

- [x] Add typed dataclasses for identity, composition, palette roles/metrics, typography confidence, geometry, annotations, hierarchy, style, constraints, embeddings and per-field confidence. Keep every field JSON-compatible and preserve unknown metadata outside the typed core under `extensions`.
- [x] Add `StyleCapsule`, `DesignPacket`, `DesignPatch`, `RenderTrace`, `ScientificContract`, `JournalProfile`, `PreferencePair` and `QAReport` hard/soft sections to the existing contract exports without creating a parallel renderer contract.
- [x] Update the JSON schema and contract documentation to require contract name/schema version and to describe the new payloads.
- [x] Keep existing persisted session schema readable while emitting the new contracts in current artifacts.

### Task 2: Add source-specific reference analyzers and DNA builder

**Files:**
- Create: `src/publication_figure_design/reference_intelligence/analyzers/raster.py`
- Create: `src/publication_figure_design/reference_intelligence/analyzers/svg.py`
- Create: `src/publication_figure_design/reference_intelligence/analyzers/pdf.py`
- Create: `src/publication_figure_design/reference_intelligence/analyzers/code.py`
- Create: `src/publication_figure_design/reference_intelligence/dna_builder.py`
- Modify: `scripts/reference_image_analysis.py`
- Modify: `scripts/reference_library.py`

**Interfaces:**
- `analyze_reference(path: Path, *, metadata: Mapping[str, Any] | None = None) -> ReferenceDNA`
- `build_reference_dna(reference_dir: Path) -> Path`
- `ReferenceLibrary.analyze_dna(reference_id: str) -> ReferenceDNA`

- [x] Route `.png/.jpg/.jpeg` to raster analysis, `.svg` to SVG geometry/text analysis, `.pdf` to PyMuPDF when installed, and plotting code to a constrained AST/token analyzer that never executes code.
- [x] Reuse existing image analysis for palette, occupancy, whitespace, edges and aspect ratio; add panel boxes, alignment lines, geometry distributions, annotation hints and typography confidence.
- [x] Implement perceptual color conversion with a standard-library/NumPy fallback and optional `colorspacious` adapter; record role, Lab/CAM02-like coordinates, area share, contrast, CVD/grayscale status and confidence.
- [x] Write `reference_dna.json` beside each reference and link it from metadata/registry.
- [x] Keep exact font/stroke values only for vector/code inputs; raster outputs use `family_class`, relative sizes and confidence.

### Task 3: Replace metadata-proxy indexes with transparent hybrid retrieval

**Files:**
- Create: `src/publication_figure_design/reference_intelligence/embeddings.py`
- Create: `src/publication_figure_design/reference_intelligence/retrieval.py`
- Create: `src/publication_figure_design/reference_intelligence/rerank.py`
- Modify: `scripts/build_reference_indexes.py`
- Modify: `scripts/reference_library.py`
- Modify: `src/publication_figure_design/references/retrieval/multi_role.py`
- Modify: `indexes/README.md`

**Interfaces:**
- `build_hybrid_index(root: Path) -> dict[str, Any]`
- `HybridRetriever.search(task: Mapping[str, Any], role: str, limit: int = 3) -> list[dict[str, Any]]`
- `assign_reference_roles(task: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]`

- [x] Remove `deterministic-metadata-proxy` as the active index identity; emit a concrete semantic/visual/structure/style index version and build metadata.
- [x] Implement metadata, semantic text, visual structure, StyleDNA and task-compatibility signals with deterministic NumPy cosine/rule scoring as the default.
- [x] Add optional SigLIP2/DINO adapter discovery without making model downloads or Torch core dependencies.
- [x] Keep full-corpus NumPy search for current scale and record role-specific scores/reasons; formal recommendations still require benchmarked/production references.
- [x] Make role assignment explicitly independent for structure/style/palette/component/annotation and reject one-reference-for-all plans unless the task has only one role.

### Task 4: Journal profiles, StyleCapsules and style compiler integration

**Files:**
- Create: `profiles/journals/generic.yaml`
- Create: `profiles/journals/nature/initial_submission.yaml`
- Create: `profiles/journals/nature/final_submission.yaml`
- Create: `profiles/journals/nature/extended_data.yaml`
- Create: `profiles/journals/cell/final_submission.yaml`
- Create: `profiles/journals/science/final_submission.yaml`
- Create: `profiles/style-capsules/restrained-editorial.yaml`
- Create: `profiles/style-capsules/clean-clinical.yaml`
- Create: `profiles/style-capsules/dense-omics.yaml`
- Create: `profiles/style-capsules/soft-mechanism.yaml`
- Create: `profiles/style-capsules/minimal-comparison.yaml`
- Modify: `src/publication_figure_design/style/compiler.py`
- Create: `src/publication_figure_design/style/capsules.py`
- Create: `src/publication_figure_design/style/journals.py`
- Modify: `references/journal-specs.md`

**Interfaces:**
- `load_journal_profile(name: str, stage: str) -> JournalProfile`
- `load_style_capsule(name: str) -> StyleCapsule`
- `compile_design_style(journal: JournalProfile, capsule: StyleCapsule, reference: ReferenceDNA, overrides: Mapping[str, Any]) -> StyleSpec`

- [x] Separate required/recommended/house_default values with unit, source, date and applicability.
- [x] Move existing visual defaults into capsules and compile them into the existing StyleSpec; do not add a second renderer style API.
- [x] Make typography, palette, spacing, legend and geometry tokens measurable and explicit, including negative rules.
- [x] Ensure Matplotlib, SVG and existing R-facing output all consume the same compiled StyleSpec.

### Task 5: DesignPacket, candidate generation and deterministic DesignPatch repair

**Files:**
- Create: `src/publication_figure_design/design/compiler.py`
- Create: `src/publication_figure_design/design/patches.py`
- Create: `src/publication_figure_design/design/candidates.py`
- Modify: `src/publication_figure_design/orchestrator/runtime.py`
- Modify: `src/publication_figure_design/orchestrator/machine.py`
- Modify: `manifest.yaml`
- Modify: `SKILL.md`

**Interfaces:**
- `compile_design_packet(task, source, references, journal, capsule) -> DesignPacket`
- `generate_candidates(packet, mode: str = "publication") -> CandidateSet`
- `apply_design_patch(packet, patch: DesignPatch) -> DesignPacket`

- [x] Add fast/standard/publication modes; publication creates A structure-first, B style-first and C balanced low-DPI candidates with identical scientific inputs.
- [x] Convert reference observations to must-match/must-avoid, layout constraints and token bindings.
- [x] Replace prose critique outputs with machine-editable DesignPatch operations (`set`, `adjust`, `move`, `remove`, `add`) and reason codes.
- [x] Make Repair apply patches deterministically and record iteration history in the session.

### Task 6: Constraint layout primitives and vector-first assembly path

**Files:**
- Create: `src/publication_figure_design/layout/primitives.py`
- Create: `src/publication_figure_design/layout/constraints.py`
- Create: `src/publication_figure_design/layout/solver.py`
- Create: `src/publication_figure_design/renderers/svg.py`
- Create: `src/publication_figure_design/renderers/assembler.py`
- Modify: `src/publication_figure_design/render_contract.py`
- Modify: `references/backend-selection.md`

**Interfaces:**
- `SolvedLayout = solve_layout(packet: DesignPacket) -> SolvedLayout`
- `assemble_svg(panels: Sequence[Path], layout: SolvedLayout, output: Path) -> Path`

- [x] Define Canvas/PanelBox/PlotBox/LegendBox/ColorbarBox/TextBox/AnnotationBox/Gutter/Margin/AlignmentGuide in millimetres/points.
- [x] Implement required constraints with a deterministic direct solver and optional kiwisolver adapter; simple figures continue to use Matplotlib constrained layout.
- [x] Add SVG-first assembly contract and preserve editable text metadata; do not rasterize mixed R/Python panels by default.

### Task 7: Four-layer QA, RenderTrace and anti-copy gate

**Files:**
- Create: `src/publication_figure_design/qa/technical.py`
- Create: `src/publication_figure_design/qa/scientific.py`
- Create: `src/publication_figure_design/qa/geometry.py`
- Create: `src/publication_figure_design/qa/typography.py`
- Create: `src/publication_figure_design/qa/color.py`
- Create: `src/publication_figure_design/qa/perceptual.py`
- Create: `src/publication_figure_design/qa/export.py`
- Create: `src/publication_figure_design/qa/anti_copy.py`
- Modify: `src/publication_figure_design/qa/compare.py`
- Modify: `src/publication_figure_design/contracts/models.py`
- Modify: `scripts/qa_validator.py`
- Modify: `scripts/check_reference_fidelity.py`

**Interfaces:**
- `run_hard_qa(figure, packet, trace) -> dict`
- `run_scientific_qa(contract, trace) -> dict`
- `run_structural_qa(figure, reference_dna) -> dict`
- `run_perceptual_qa(figure, reference_dna) -> dict`
- `anti_copy_check(source, candidate) -> dict`

- [x] Split L0 technical, L1 scientific, L2 structural and L3 perceptual outputs; keep L0/L1 hard gates and L3 soft metrics.
- [x] Preserve the current lightweight comparison as L2 whole-image baseline, then add panel/plot/legend/annotation regions and multi-scale measurements.
- [x] Add RenderTrace records for every plotted artist with data source, columns, transform/statistic, uncertainty, bbox and style token ids.
- [x] Add anti-copy comparison for perceptual hash, crop similarity, topology, text duplication and geometric placement; allow style logic but block copied scientific content/assets.

### Task 8: Activation evals, preference data and benchmark/release routing

**Files:**
- Create: `evals/activation/train.jsonl`
- Create: `evals/activation/validation.jsonl`
- Create: `evals/activation/holdout.jsonl`
- Create: `src/publication_figure_design/evals/preference.py`
- Modify: `scripts/evaluate_benchmark.py`
- Modify: `scripts/evaluate_holdout.py`
- Modify: `scripts/ci_gate.py`
- Modify: `assets/reference-benchmarks/golden_tasks.json`
- Create: `assets/reference-benchmarks/preference_pairs.jsonl`

**Interfaces:**
- `score_preference_pair(pair, scores) -> dict`
- `evaluate_activation_split(path) -> dict`
- `run_eval(mode: str) -> int` where mode is `quick|full|visual|release`

- [x] Add positive/negative/near-miss activation cases and train/validation/holdout split metadata.
- [x] Add pairwise preference records and Elo/Bradley-Terry-compatible aggregation with reason taxonomy and Champion/Challenger/Rejected states.
- [x] Keep hidden holdout and generation corpus gates separate; add human preference win-rate and repair iteration/render failure metrics without replacing scientific or hard QA gates.
- [x] Make `pfd eval quick|full|visual|release` explicit and make `release` invoke the same gate as CI.

### Task 9: Dependency extras, package boundary and old-path cleanup

**Files:**
- Modify: `pyproject.toml`
- Modify: `requirements.txt`
- Modify: `requirements-reference.txt`
- Modify: `src/publication_figure_design/cli.py`
- Move/remove: core logic currently duplicated in `scripts/reference_library.py`, `scripts/build_reference_indexes.py`, `scripts/style_compiler.py`, and `scripts/qa_validator.py` after callers are migrated
- Modify: `README.md`, `README_EN.md`, `CONTRIBUTING.md`, `manifest.yaml`
- Remove: stale metadata-proxy references, old command aliases, duplicate style/index implementations and obsolete docs that point to them

- [x] Define `core`, `render-python`, `reference-analysis`, `reference-ml`, `perceptual`, `vector`, and `dev` extras; keep Torch/model packages optional.
- [x] Move production logic into `src/` and leave scripts as thin wrappers with no `sys.path` injection from package CLI.
- [x] Update all docs, adapters and manifest routes to the one current path; remove replaced files and dead tests only after call sites are migrated.
- [x] Rebuild indexes and generated adapters from the canonical implementation.

### Task 10: Unified final verification

**Files:**
- Modify: `.github/workflows/validation.yml`
- Modify: `references/runtime-environment.md`
- Modify: `scripts/check_skill_contract.py`

- [x] Add contract checks for DNA, capsules, profiles, patches, trace, QA layers, activation splits and eval modes.
- [x] Run all repository tests and release gate through `D:\Anaconda\envs\piepaper\python.exe` only after Tasks 1–9 are complete.
- [x] Run reference validation, DNA coverage, index build, retrieval benchmark, holdout, adversarial, fidelity, quarantine, adapter canary, lifecycle canary and `git diff --check`.
- [x] Confirm no old interface/import/metadata-proxy production references remain and no dirty generated artifacts are accidental; intended implementation changes remain available for the user's commit/review.
