"""Load and compile measurable house-style capsules."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from ..reference_intelligence.dna import ReferenceDNA, StyleCapsule
from .compiler import StyleSpec


ROOT = Path(__file__).resolve().parents[3]


def load_style_capsule(name: str, *, root: Path = ROOT) -> StyleCapsule:
    path = root / "profiles" / "style-capsules" / (name if name.endswith(".yaml") else f"{name}.yaml")
    if not path.is_file():
        raise FileNotFoundError(f"unknown style capsule: {name}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return StyleCapsule(name=str(payload.get("name", path.stem)), **{key: payload.get(key, {}) for key in ("visual_hierarchy", "palette", "typography", "geometry", "spacing", "legend")}, negative_rules=list(payload.get("negative_rules", [])), source_ids=list(payload.get("source_ids", [])))


def compile_style_capsule(capsule: StyleCapsule, reference: ReferenceDNA | Mapping[str, Any] | None = None, overrides: Mapping[str, Any] | None = None) -> StyleSpec:
    reference_data = reference.to_dict() if isinstance(reference, ReferenceDNA) else dict(reference or {})
    palette = dict(capsule.palette)
    palette.update(dict((reference_data.get("palette") or {}).get("semantic_roles") or {}))
    typography = dict(capsule.typography)
    typography.update(dict(reference_data.get("typography") or {}))
    geometry = dict(capsule.geometry)
    geometry.update(dict(reference_data.get("geometry") or {}))
    spacing = dict(capsule.spacing)
    spacing.update(dict(reference_data.get("composition") or {}).get("gutters", {}))
    payload = {
        "canvas": {"background": palette.get("background", "#FFFFFF")},
        "panel": {"background": palette.get("background", "#FFFFFF")},
        "palette": {"roles": palette.get("semantic_roles", palette.get("roles", {}))},
        "typography": typography,
        "stroke": geometry,
        "spacing": spacing,
        "legend": capsule.legend,
        "negative_rules": capsule.negative_rules,
    }
    payload.update(dict(overrides or {}))
    return StyleSpec.from_dict(payload)
