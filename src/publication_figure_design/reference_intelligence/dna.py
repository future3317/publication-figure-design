"""Typed, measurable reference intelligence contracts.

The contracts intentionally accept conservative evidence.  Raster inputs may
describe relative typography and heuristic geometry, while vector/code inputs
may provide exact measurements.  No field is promoted to exact without a
source-specific confidence record.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


def _dict(value: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return dict(value or {})


def _list(value: Sequence[Any] | None = None) -> list[Any]:
    return list(value or [])


@dataclass
class ReferenceDNA:
    schema: str = "publication-figure-design/reference-dna"
    schema_version: str = "2.0"
    identity: dict[str, Any] = field(default_factory=dict)
    composition: dict[str, Any] = field(default_factory=dict)
    palette: dict[str, Any] = field(default_factory=dict)
    typography: dict[str, Any] = field(default_factory=dict)
    geometry: dict[str, Any] = field(default_factory=dict)
    annotations: dict[str, Any] = field(default_factory=dict)
    hierarchy: dict[str, Any] = field(default_factory=dict)
    style: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    embeddings: dict[str, Any] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)
    extensions: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_metadata(cls, metadata: Mapping[str, Any], *, card: Mapping[str, Any] | None = None) -> "ReferenceDNA":
        meta = dict(metadata)
        card = dict(card or {})
        canvas = dict(card.get("canvas") or {})
        panels = dict(card.get("panels") or {})
        geometry = dict(card.get("geometry") or {})
        palette = dict(card.get("palette") or {})
        grammar = dict(meta.get("visual_grammar") or {})
        return cls(
            identity={
                "id": meta.get("id", ""), "source": meta.get("source", ""),
                "license": meta.get("license", "unknown"), "journal": meta.get("journal_style", ""),
                "year": meta.get("year"), "figure_family": meta.get("figure_type", ""),
                "source_kind": meta.get("reference_kind", "raster"),
            },
            composition={
                "aspect_ratio": canvas.get("aspect_ratio", meta.get("aspect_ratio")),
                "panel_count": panels.get("count", meta.get("panel_count", 1)),
                "panel_bboxes": panels.get("bboxes_px", []),
                "panel_area_ratios": panels.get("area_ratios", []),
                "reading_order": panels.get("reading_order", []),
                "hero_panel": panels.get("hero_panel"),
                "gutters": panels.get("gutters", {}),
                "outer_margins": panels.get("outer_margins", {}),
                "alignment_lines": panels.get("alignment_lines", []),
                "whitespace_regions": card.get("whitespace_map", {}),
            },
            palette={
                "background": (card.get("background") or {}).get("hex"),
                "dominant": palette.get("dominant", []),
                "neutrals": palette.get("neutrals", []),
                "categorical": palette.get("categorical", []),
                "sequential": palette.get("sequential", []),
                "diverging": palette.get("diverging", []),
                "accent": palette.get("accent"),
                "semantic_roles": grammar.get("palette_roles", meta.get("palette_roles", {})),
                "area_share": palette.get("area_share", {}),
                "perceptual_distance": palette.get("perceptual_distance", {}),
                "cvd_score": palette.get("cvd_score"),
                "grayscale_score": palette.get("grayscale_score"),
            },
            typography={
                "family_class": (card.get("typography") or {}).get("font_family", "sans_serif_unknown"),
                "title_body_ratio": (card.get("typography") or {}).get("title_body_ratio"),
                "axis_tick_ratio": (card.get("typography") or {}).get("axis_tick_ratio"),
                "panel_label_style": (card.get("typography") or {}).get("panel_label_style"),
                "weight": (card.get("typography") or {}).get("weight"),
                "line_height": (card.get("typography") or {}).get("line_height"),
                "text_density": (card.get("typography") or {}).get("text_density"),
                "alignment": (card.get("typography") or {}).get("alignment"),
                "exact_font": meta.get("font_family") if meta.get("source_kind") in {"svg", "pdf", "code"} else None,
            },
            geometry={
                "stroke_width_distribution": (card.get("stroke_width_px") or {}).get("distribution", (card.get("stroke_width_px") or {}).get("median")),
                "marker_family": card.get("marker_family", grammar.get("chart_marks_axes")),
                "marker_size_distribution": (card.get("marker_family") or {}).get("size_distribution"),
                "corner_radius": (card.get("geometry") or {}).get("corner_radius"),
                "arrowhead": grammar.get("connectors", {}).get("arrowhead") if isinstance(grammar.get("connectors"), dict) else None,
                "leader_style": grammar.get("annotations_typography", {}).get("leader_style") if isinstance(grammar.get("annotations_typography"), dict) else None,
                "spine_model": (card.get("axes") or {}).get("spines"),
                "grid_model": (card.get("axes") or {}).get("grid_proxy"),
            },
            annotations={
                "direct_labels": grammar.get("annotations_typography", {}).get("direct_labels") if isinstance(grammar.get("annotations_typography"), dict) else None,
                "brackets": grammar.get("annotations_typography", {}).get("brackets") if isinstance(grammar.get("annotations_typography"), dict) else None,
                "callouts": grammar.get("annotations_typography", {}).get("callouts") if isinstance(grammar.get("annotations_typography"), dict) else None,
                "leaders": grammar.get("annotations_typography", {}).get("leaders") if isinstance(grammar.get("annotations_typography"), dict) else None,
                "significance": grammar.get("annotations_typography", {}).get("significance") if isinstance(grammar.get("annotations_typography"), dict) else None,
                "clearance": grammar.get("annotations_typography", {}).get("clearance") if isinstance(grammar.get("annotations_typography"), dict) else None,
            },
            hierarchy={
                "focal_regions": (card.get("saliency") or {}).get("bbox_px"),
                "saliency_distribution": card.get("saliency"),
                "visual_weight": grammar.get("visual_hierarchy"),
                "density": card.get("visual_density", meta.get("data_density")),
                "data_to_ink_proxy": card.get("ink_coverage"),
            },
            style={
                "aesthetic_tags": meta.get("tags", []),
                "style_cluster": meta.get("style_cluster"),
                "style_vector": meta.get("style_vector"),
                "quality_score": meta.get("aesthetic_quality", meta.get("aesthetic_rating")),
            },
            constraints={
                "must_match": meta.get("must_match", []),
                "must_avoid": meta.get("must_avoid", []),
            },
            embeddings={
                "semantic_embedding": meta.get("semantic_embedding"),
                "visual_embedding": meta.get("visual_embedding"),
                "structure_embedding": meta.get("structure_embedding"),
            },
            confidence=dict(meta.get("confidence") or {}),
            extensions={"visual_grammar": grammar, "figure_card": card},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema, "schema_version": self.schema_version,
            "identity": self.identity, "composition": self.composition,
            "palette": self.palette, "typography": self.typography,
            "geometry": self.geometry, "annotations": self.annotations,
            "hierarchy": self.hierarchy, "style": self.style,
            "constraints": self.constraints, "embeddings": self.embeddings,
            "confidence": self.confidence, "extensions": self.extensions,
        }

    def validate(self) -> list[str]:
        failures: list[str] = []
        for section in ("identity", "composition", "palette", "typography", "geometry", "annotations", "hierarchy", "style", "constraints", "embeddings", "confidence"):
            if not isinstance(getattr(self, section), dict):
                failures.append(f"{section} must be an object")
        if self.schema_version != "2.0":
            failures.append("reference DNA schema_version must be 2.0")
        return failures


@dataclass
class StyleCapsule:
    name: str
    visual_hierarchy: dict[str, Any] = field(default_factory=dict)
    palette: dict[str, Any] = field(default_factory=dict)
    typography: dict[str, Any] = field(default_factory=dict)
    geometry: dict[str, Any] = field(default_factory=dict)
    spacing: dict[str, Any] = field(default_factory=dict)
    legend: dict[str, Any] = field(default_factory=dict)
    negative_rules: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "visual_hierarchy": self.visual_hierarchy, "palette": self.palette, "typography": self.typography, "geometry": self.geometry, "spacing": self.spacing, "legend": self.legend, "negative_rules": self.negative_rules, "source_ids": self.source_ids}


@dataclass
class JournalProfile:
    name: str
    stage: str = "final_submission"
    rules: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    source_date: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "stage": self.stage, "rules": self.rules, "source": self.source, "source_date": self.source_date}


@dataclass
class DesignPacket:
    task: dict[str, Any] = field(default_factory=dict)
    scientific_contract: dict[str, Any] = field(default_factory=dict)
    references: dict[str, Any] = field(default_factory=dict)
    journal_profile: dict[str, Any] = field(default_factory=dict)
    style_capsule: dict[str, Any] = field(default_factory=dict)
    layout_constraints: list[dict[str, Any]] = field(default_factory=list)
    style_tokens: dict[str, Any] = field(default_factory=dict)
    bindings: dict[str, Any] = field(default_factory=dict)
    must_match: list[str] = field(default_factory=list)
    must_avoid: list[str] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    patch_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"task": self.task, "scientific_contract": self.scientific_contract, "references": self.references, "journal_profile": self.journal_profile, "style_capsule": self.style_capsule, "layout_constraints": self.layout_constraints, "style_tokens": self.style_tokens, "bindings": self.bindings, "must_match": self.must_match, "must_avoid": self.must_avoid, "candidates": self.candidates, "patch_history": self.patch_history}


@dataclass
class DesignPatch:
    patches: list[dict[str, Any]] = field(default_factory=list)
    source: str = "critic"
    iteration: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"patches": self.patches, "source": self.source, "iteration": self.iteration}

    def apply(self, packet: Mapping[str, Any]) -> dict[str, Any]:
        result = deepcopy(dict(packet))
        for patch in self.patches:
            path = str(patch.get("path", "")).split(".")
            if not path or not path[0]:
                raise ValueError("design patch path is required")
            cursor: Any = result
            for key in path[:-1]:
                if not isinstance(cursor, dict):
                    raise ValueError(f"cannot descend into patch path {patch['path']!r}")
                cursor = cursor.setdefault(key, {})
            key = path[-1]
            op = patch.get("operation", "set")
            if op == "set" or op == "adjust":
                cursor[key] = patch.get("value")
            elif op == "remove":
                if isinstance(cursor, dict):
                    cursor.pop(key, None)
            elif op == "add":
                cursor.setdefault(key, []).append(patch.get("value"))
            else:
                raise ValueError(f"unsupported design patch operation {op!r}")
        return result


@dataclass
class RenderTrace:
    artists: list[dict[str, Any]] = field(default_factory=list)
    renderer: str = ""
    renderer_version: str = ""
    source_data_hash: str = ""

    def add_artist(self, *, artist_id: str, artist_type: str, data_source: str = "", x_column: str = "", y_column: str = "", group: str = "", transform: str = "", statistic: str = "", uncertainty: str = "", bbox: Mapping[str, Any] | None = None, style_token_ids: Sequence[str] | None = None) -> None:
        self.artists.append({"artist_id": artist_id, "artist_type": artist_type, "data_source": data_source, "x_column": x_column, "y_column": y_column, "group": group, "transform": transform, "statistic": statistic, "uncertainty": uncertainty, "bbox": dict(bbox or {}), "style_token_ids": list(style_token_ids or [])})

    def to_dict(self) -> dict[str, Any]:
        return {"artists": self.artists, "renderer": self.renderer, "renderer_version": self.renderer_version, "source_data_hash": self.source_data_hash}


@dataclass
class PreferencePair:
    left_id: str
    right_id: str
    winner: str
    reasons: list[str] = field(default_factory=list)
    figure_family: str = ""
    status: str = "challenger"

    def to_dict(self) -> dict[str, Any]:
        return {"left_id": self.left_id, "right_id": self.right_id, "winner": self.winner, "reasons": self.reasons, "figure_family": self.figure_family, "status": self.status}
