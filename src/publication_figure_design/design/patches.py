"""Deterministic DesignPatch application."""

from __future__ import annotations

from typing import Any

from ..reference_intelligence.dna import DesignPacket, DesignPatch


def apply_design_patch(packet: DesignPacket, patch: DesignPatch | dict[str, Any]) -> DesignPacket:
    patch_obj = patch if isinstance(patch, DesignPatch) else DesignPatch(**dict(patch))
    payload = patch_obj.apply(packet.to_dict())
    payload.setdefault("patch_history", []).append(patch_obj.to_dict())
    return DesignPacket(**{key: payload.get(key, getattr(packet, key)) for key in ("task", "scientific_contract", "references", "journal_profile", "style_capsule", "layout_constraints", "style_tokens", "bindings", "must_match", "must_avoid", "candidates", "patch_history")})
