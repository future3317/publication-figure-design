"""Compile scientific and reference contracts into a DesignPacket."""

from __future__ import annotations

from typing import Any, Mapping

from ..reference_intelligence.dna import DesignPacket, JournalProfile, ReferenceDNA, StyleCapsule
from ..style.capsules import compile_style_capsule


def _to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return dict(value or {})


def compile_design_packet(task: Mapping[str, Any], source: Mapping[str, Any] | Any, references: Mapping[str, Any] | Any, journal: JournalProfile | Mapping[str, Any], capsule: StyleCapsule | Mapping[str, Any]) -> DesignPacket:
    task_data = _to_dict(task)
    source_data = _to_dict(source)
    reference_data = _to_dict(references)
    journal_data = _to_dict(journal)
    capsule_data = _to_dict(capsule)
    dna = reference_data.get("style_reference_dna") or reference_data.get("reference_dna") or {}
    capsule_obj = capsule if isinstance(capsule, StyleCapsule) else StyleCapsule(name=str(capsule_data.get("name", "default")), **{key: capsule_data.get(key, {}) for key in ("visual_hierarchy", "palette", "typography", "geometry", "spacing", "legend")}, negative_rules=list(capsule_data.get("negative_rules", [])))
    style = compile_style_capsule(capsule_obj, dna)
    packet = DesignPacket(
        task=task_data,
        scientific_contract=source_data,
        references=reference_data,
        journal_profile=journal_data,
        style_capsule=capsule_data,
        layout_constraints=list(reference_data.get("layout_constraints", [])),
        style_tokens=style.to_dict(),
        bindings=dict(source_data.get("bindings", {})),
        must_match=list(reference_data.get("must_match", [])),
        must_avoid=list(reference_data.get("must_avoid", []) + capsule_data.get("negative_rules", [])),
    )
    packet.layout_constraints.extend([
        {"path": "typography.min_font_pt", "operator": ">=", "value": journal_data.get("rules", {}).get("min_font_pt", {}).get("value", 5)},
        {"path": "layout.gutter", "operator": ">=", "value": capsule_data.get("spacing", {}).get("panel_gap_ratio", 0.04)},
    ])
    return packet
