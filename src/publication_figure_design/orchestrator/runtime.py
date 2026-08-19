"""CLI runtime handlers that connect task metadata to existing skill scripts.

The state machine remains backend-agnostic; these handlers make the shipped CLI
useful without pretending that a missing source or render is complete. Supplied
artifacts are measured and carried forward, while absent optional inputs are
recorded as ``not_provided`` for the agent to repair or fill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ..contracts import ReferenceSet, SourceSpec, TaskSpec
from .machine import Orchestrator, StageContext


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
        ids = metadata.get("reference_ids") or metadata.get("references") or []
        if isinstance(ids, str):
            ids = [ids]
        ids = [str(value) for value in ids]
        references = ReferenceSet(candidates=[{"id": value} for value in ids])
    return {"status": "ready" if references.candidates or references.structure_reference else "not_provided", "reference_set": references.to_dict()}


def _inspect(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    images = metadata.get("reference_images") or metadata.get("reference_image") or []
    if isinstance(images, (str, Path)):
        images = [images]
    if not images:
        return {"status": "not_provided", "cards": []}
    from reference_image_analysis import analyze_image

    cards = []
    for image in images:
        path = Path(image)
        if not path.is_file():
            cards.append({"image": str(path), "status": "missing"})
            continue
        cards.append(analyze_image(path, figure_type=str(metadata.get("figure_type", "unknown"))))
    return {"status": "ready" if all(card.get("status", "ready") != "missing" for card in cards) else "blocked", "cards": cards}


def _carry(stage: str):
    def handler(context: StageContext) -> dict[str, Any]:
        metadata = _metadata(context)
        supplied = metadata.get(f"{stage.lower().replace(' ', '_')}_artifact") or metadata.get(stage.lower().replace(" ", "_"))
        return {"status": "ready" if supplied is not None else "not_provided", "artifact": supplied}
    return handler


def _compare(context: StageContext) -> dict[str, Any]:
    metadata = _metadata(context)
    reference = metadata.get("reference_image")
    candidate = metadata.get("candidate_image") or metadata.get("after_image")
    if not reference or not candidate:
        return {"status": "not_provided", "comparison": None}
    from compare_output_to_reference import compare_output_to_reference

    return {"status": "ready", "comparison": compare_output_to_reference(reference, candidate)}


def build_runtime_orchestrator() -> Orchestrator:
    """Build the production CLI orchestrator with script-backed handlers."""
    from .machine import WorkflowStage

    handlers = {
        WorkflowStage.ROUTE: _route,
        WorkflowStage.INTAKE: _intake,
        WorkflowStage.REFERENCE_RETRIEVAL: _retrieve,
        WorkflowStage.REFERENCE_INSPECTION: _inspect,
        WorkflowStage.DESIGN_SPEC: _carry("design_spec"),
        WorkflowStage.BINDING: _carry("binding_map"),
        WorkflowStage.RENDER: _carry("render_plan"),
        WorkflowStage.COMPARE: _compare,
        WorkflowStage.CRITIQUE: _carry("critique"),
        WorkflowStage.REPAIR: _carry("repair"),
        WorkflowStage.QA: _carry("qa_report"),
        WorkflowStage.EXPORT: _carry("export_manifest"),
    }
    return Orchestrator(handlers=handlers)
