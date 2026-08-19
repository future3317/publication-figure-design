"""Validate the compact observation card used for a concrete visual reference."""

from __future__ import annotations

from typing import Any


NOT_PRESENT = "not_present"

SECTION_FIELDS = {
    "canvas_composition": (
        "aspect_and_panel_layout", "visual_hierarchy", "alignment_and_spacing",
    ),
    "connectors": (
        "geometry", "direction_and_arrowhead", "stroke", "anchors_and_routing", "layering",
    ),
    "objects_material": (
        "shape_and_projection", "fill_and_material", "outline_and_edges", "depth_cues",
        "placement_and_scale",
    ),
    "repetition_structures": (
        "topology", "count_spacing_rhythm", "grouping_and_alignment", "variation_and_emphasis",
    ),
    "palette_roles": (
        "background", "roles_and_proportions", "contrast_and_emphasis",
    ),
    "annotations_typography": (
        "text_hierarchy", "callouts_and_leaders", "placement_and_clearance",
    ),
    "legend_key": (
        "scope", "placement", "entries_and_encoding", "frame_treatment",
    ),
    "chart_marks_axes": (
        "marks_and_encoding", "axes_and_scales", "guides_and_grid",
    ),
}

REQUIRED_PRESENT_SECTIONS = {"canvas_composition", "palette_roles"}


def _filled(value: Any) -> bool:
    return bool(value.strip()) if isinstance(value, str) else bool(value)


def validate_visual_grammar(card: Any) -> list[str]:
    """Return human-actionable omissions in an observation card.

    A non-applicable visual family is recorded as ``not_present``.  When it is
    present, the card must spell out the observations a renderer needs instead
    of collapsing them into an adjective such as "clean" or "professional".
    """
    if not isinstance(card, dict):
        return ["Visual grammar observation card is missing."]

    errors: list[str] = []
    for section, fields in SECTION_FIELDS.items():
        value = card.get(section)
        if value == NOT_PRESENT:
            if section in REQUIRED_PRESENT_SECTIONS:
                errors.append(f"Visual grammar '{section}' cannot be not_present.")
            continue
        if not isinstance(value, dict):
            errors.append(f"Visual grammar section '{section}' must be an object or not_present.")
            continue
        missing = [field for field in fields if not _filled(value.get(field))]
        if missing:
            errors.append(f"Visual grammar section '{section}' is missing: " + ", ".join(missing) + ".")

    must_match = card.get("must_match")
    if not isinstance(must_match, list) or not all(_filled(item) for item in must_match):
        errors.append("Visual grammar must_match must be a non-empty list of observable features.")
    return errors
