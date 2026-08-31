"""CLI runtime handlers that connect task metadata to existing skill scripts.

The state machine remains backend-agnostic; these handlers make the shipped CLI
useful without pretending that a missing source or render is complete. Supplied
artifacts are measured and carried forward, while absent optional inputs are
recorded as ``not_provided`` for the agent to repair or fill.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ..contracts import ReferenceSet, SourceSpec, TaskSpec
from ..reference_intelligence import RenderTrace
from .machine import GateResult, Orchestrator, StageContext


def _max_repairs() -> int:
    """Read the sprint stop rule from the canonical Champion Board config."""
    root = Path(__file__).resolve().parents[3]
    payload = json.loads((root / "assets" / "reference-benchmarks" / "champion_board.json").read_text(encoding="utf-8"))
    repairs = int(payload["focus"]["max_repairs"])
    if repairs < 0:
        raise ValueError("champion board max_repairs must be non-negative")
    return repairs


def _metadata(context: StageContext) -> dict[str, Any]:
    value = context.task.get("metadata", {})
    return dict(value) if isinstance(value, Mapping) else {}


def _route(context: StageContext) -> dict[str, Any]:
    return {"status": "routed", "task": context.task, "mode": context.task.get("mode", "create")}


def _intake(context: StageContext) -> dict[str, Any]:
    data = _metadata(context).get("source") or _metadata(context).get("source_spec")
    if isinstance(data, Mapping):
        source = SourceSpec.from_dict(data)
        return {"status": "ready", "source": source.to_dict()}
    return {"status": "not_provided", "source": SourceSpec().to_dict()}


def _retrieve(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    data = metadata.get("reference_set")
    if isinstance(data, Mapping):
        references = ReferenceSet.from_dict(data)
    else:
        # Resume is deterministic: once a session has selected references, the
        # retrieval stage reuses those ids instead of sampling the pool again.
        ids = context.telemetry.get("selected_reference_ids") or metadata.get("reference_ids") or metadata.get("references") or []
        if isinstance(ids, str):
            ids = [ids]
        ids = [str(value) for value in ids]
        references = ReferenceSet(candidates=[{"id": value} for value in ids])
    hybrid_result = None
    if not references.candidates and metadata.get("figure_type"):
        try:
            from ..references.retrieval.multi_role import MultiRoleReferenceRetriever
            hybrid_result = MultiRoleReferenceRetriever().retrieve_hybrid(
                figure_type=str(metadata.get("figure_type")),
                tags=metadata.get("tags", []),
                layout=metadata.get("layout"),
                limit=3,
            )
            candidates = hybrid_result.get("structure_reference", [])
            references = ReferenceSet(
                structure_reference=str(candidates[0]["id"]) if candidates else "",
                style_reference=str((hybrid_result.get("style_reference") or [{}])[0].get("id", "")),
                component_references=[str(row["id"]) for row in hybrid_result.get("component_references", [])],
                annotation_reference=str((hybrid_result.get("annotation_reference") or [{}])[0].get("id", "")),
                palette_reference=str((hybrid_result.get("palette_reference") or [{}])[0].get("id", "")),
                candidates=candidates,
                selection_reason="hybrid metadata + semantic + structure + style role assignment",
            )
        except (ImportError, OSError, ValueError):
            hybrid_result = None
    role_fields = {
        "structure_reference": references.structure_reference,
        "style_reference": references.style_reference,
        "component_references": references.component_references,
        "annotation_reference": references.annotation_reference,
        "palette_reference": references.palette_reference,
    }
    selected_roles = {
        role: ([str(value)] if isinstance(value, str) and value else [str(item) for item in value if item])
        for role, value in role_fields.items()
    }
    top_k_ids = [
        str(row.get("id"))
        for row in references.candidates
        if isinstance(row, Mapping) and row.get("id")
    ]
    if hybrid_result:
        for rows in hybrid_result.values():
            if isinstance(rows, list):
                top_k_ids.extend(
                    str(row.get("id"))
                    for row in rows
                    if isinstance(row, Mapping) and row.get("id")
                )
    top_k_ids = list(dict.fromkeys(top_k_ids))
    selected_ids = list(dict.fromkeys(value for values in selected_roles.values() for value in values))
    return {
        "status": "ready" if references.candidates or references.structure_reference else "not_provided",
        "reference_set": references.to_dict(),
        "reference_index_version": context.telemetry.get("reference_index_version", "unknown"),
        "deterministic_resume": bool(context.telemetry.get("selected_reference_ids")),
        "hybrid_candidates": hybrid_result or {},
        "selection_trace": {
            "task_id": str(context.task.get("task_id", context.session_id)),
            "figure_family": str(metadata.get("figure_family") or metadata.get("visual_family") or metadata.get("figure_type", "")),
            "selected_reference_ids": selected_ids,
            "selected_roles": selected_roles,
            "top_k_ids": top_k_ids,
        },
    }


def _inspect(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    images = metadata.get("reference_images") or metadata.get("reference_image") or []
    if isinstance(images, (str, Path)):
        images = [images]
    if not images:
        return {"status": "not_provided", "cards": []}
    from ..reference_intelligence.analyzers.raster import analyze_raster

    cards = []
    for image in images:
        path = Path(image)
        if not path.is_file():
            cards.append({"image": str(path), "status": "missing"})
            continue
        dna = analyze_raster(path, metadata=metadata)
        cards.append({"figure_card": dna.extensions.get("figure_card", {}), "reference_dna": dna.to_dict()})
    return {"status": "ready" if all(card.get("status", "ready") != "missing" for card in cards) else "blocked", "cards": cards}


def _carry(stage: str):
    def handler(context: StageContext) -> dict[str, Any]:
        metadata = _metadata(context)
        supplied = metadata.get(f"{stage.lower().replace(' ', '_')}_artifact") or metadata.get(stage.lower().replace(" ", "_"))
        return {"status": "ready" if supplied is not None else "not_provided", "artifact": supplied}
    return handler


def _design_spec(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    packet = metadata.get("design_packet")
    if packet is not None:
        return {"status": "ready", "design_packet": packet}
    from ..design.compiler import compile_design_packet
    from ..profiles.domains import load_domain_profile
    from ..style.capsules import load_style_capsule
    from ..style.journals import load_journal_profile
    task = {**context.task, **metadata}
    capsule_name = str(metadata.get("style_capsule", "restrained-editorial"))
    journal_name = str(metadata.get("journal", "generic"))
    domain_name = metadata.get("domain")
    capsule = load_style_capsule(capsule_name)
    journal = load_journal_profile(journal_name, str(metadata.get("submission_stage", "final_submission")))
    domain = load_domain_profile(str(domain_name)) if domain_name else None
    packet = compile_design_packet(task, metadata.get("source", {}), metadata.get("reference_set", {}), journal, capsule, domain)
    from ..design.candidates import generate_candidates
    generate_candidates(packet, str(metadata.get("generation_mode", "publication")))
    result = {
        "status": "ready",
        "design_packet": packet.to_dict(),
        "journal_profile": journal.to_dict(),
        "style_capsule": capsule.to_dict(),
    }
    if domain is not None:
        result["domain_profile"] = domain
    return result


def _binding(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    binding = metadata.get("binding_map") or metadata.get("bindings")
    if binding is None:
        source = metadata.get("source", {})
        binding = {"bindings": source.get("variable_roles", {}), "unresolved_orphan_series": []}
    return {"status": "ready", "binding_map": binding}


def _compare(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    reference = metadata.get("reference_image")
    candidate = metadata.get("candidate_image") or metadata.get("after_image")
    if not reference or not candidate:
        return {"status": "not_provided", "comparison": None}
    from ..qa.compare import compare_output_to_reference
    return {"status": "ready", "comparison": compare_output_to_reference(reference, candidate)}


def _render(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    supplied = metadata.get("render_plan") or metadata.get("render")
    if supplied is None:
        return {"status": "not_provided", "render_plan": None}
    if not isinstance(supplied, Mapping):
        return {"status": "blocked", "errors": ["render_plan must be an object"]}
    try:
        from ..render_contract import validate_render_contract
    except ImportError:  # direct script execution keeps the adapter path usable
        from render_contract import validate_render_contract

    reference_led = bool(metadata.get("reference_led") or metadata.get("reference_image") or metadata.get("reference_ids"))
    passed, failures = validate_render_contract(supplied, reference_led=reference_led)
    trace = metadata.get("render_trace") or {"artists": [], "renderer": supplied.get("backend", ""), "renderer_version": supplied.get("renderer_version", "")}
    if not isinstance(trace, Mapping):
        return {"status": "blocked", "errors": ["render_trace must be an object"]}
    return {
        "status": "ready" if passed else "blocked",
        "render_plan": dict(supplied),
        "reference_led": reference_led,
        "consumed_specs": supplied.get("consumed_specs", []),
        "errors": failures,
        "render_trace": dict(trace),
    }


def _critique(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    patch = metadata.get("design_patch") or metadata.get("critique_patch")
    if patch is None:
        return {"status": "not_provided", "design_patch": None}
    if not isinstance(patch, Mapping) or not isinstance(patch.get("patches", []), list):
        return {"status": "blocked", "errors": ["design_patch must contain a patches list"]}
    return {"status": "ready", "design_patch": dict(patch), "machine_editable": True}


def _repair(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    patch = metadata.get("design_patch") or metadata.get("critique_patch")
    packet = metadata.get("design_packet")
    if patch is None or packet is None:
        return {"status": "not_provided", "design_packet": packet, "applied_patch": patch}
    try:
        from ..design.patches import apply_design_patch
        from ..reference_intelligence import DesignPacket
        packet_obj = DesignPacket(**{key: packet.get(key, getattr(DesignPacket(), key)) for key in ("task", "scientific_contract", "references", "journal_profile", "style_capsule", "layout_constraints", "style_tokens", "bindings", "must_match", "must_avoid", "candidates", "patch_history")})
        updated = apply_design_patch(packet_obj, dict(patch)).to_dict()
    except (TypeError, ValueError, KeyError) as exc:
        return {"status": "blocked", "errors": [str(exc)]}
    return {"status": "ready", "design_packet": updated, "applied_patch": patch}


def _qa(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    figure = metadata.get("candidate_image") or metadata.get("output_image")
    trace = metadata.get("render_trace") or {}
    packet = metadata.get("design_packet") or {}
    if not figure and not packet and not trace:
        return {"status": "not_provided", "hard": {}, "scientific": {}, "structural": {}, "perceptual": {}, "passed": False}
    from ..qa import run_hard_qa, run_scientific_qa, run_structural_qa, run_perceptual_qa
    hard = run_hard_qa(figure, packet, trace) if figure else {"layer": "L0_hard_technical", "passed": False, "issues": ["figure image not provided"]}
    scientific = run_scientific_qa(packet.get("scientific_contract", {}), trace)
    compare = metadata.get("comparison") or {}
    structural = run_structural_qa(compare)
    perceptual = run_perceptual_qa(compare)
    passed = bool(hard.get("passed") and scientific.get("passed") and structural.get("passed"))
    return {"status": "ready" if passed else "blocked", "hard": hard, "scientific": scientific, "structural": structural, "perceptual": perceptual, "passed": passed}


def build_runtime_orchestrator() -> Orchestrator:
    """Build the production CLI orchestrator with script-backed handlers."""
    from .machine import WorkflowStage

    handlers = {
        WorkflowStage.ROUTE: _route,
        WorkflowStage.INTAKE: _intake,
        WorkflowStage.REFERENCE_RETRIEVAL: _retrieve,
        WorkflowStage.REFERENCE_INSPECTION: _inspect,
        WorkflowStage.DESIGN_SPEC: _design_spec,
        WorkflowStage.BINDING: _binding,
        WorkflowStage.RENDER: _render,
        WorkflowStage.COMPARE: _compare,
        WorkflowStage.CRITIQUE: _critique,
        WorkflowStage.REPAIR: _repair,
        WorkflowStage.QA: _qa,
        WorkflowStage.EXPORT: _carry("export_manifest"),
    }
    def status_gate(payload: Any) -> GateResult:
        if isinstance(payload, Mapping) and payload.get("status") == "blocked":
            return GateResult(False, "handler reported blocked", {"errors": payload.get("errors", [])})
        return GateResult(True, "handler status accepted")

    return Orchestrator(handlers=handlers, gates={WorkflowStage.RENDER: status_gate}, max_retries=_max_repairs() + 1)
