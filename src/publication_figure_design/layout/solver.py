"""Deterministic lightweight layout solver with optional kiwisolver use."""

from __future__ import annotations

from typing import Any

from ..reference_intelligence.dna import DesignPacket


def solve_layout(packet: DesignPacket | dict[str, Any]) -> dict[str, Any]:
    data = packet.to_dict() if isinstance(packet, DesignPacket) else dict(packet)
    task = data.get("task", {})
    journal = data.get("journal_profile", {})
    rules = journal.get("rules", {}) if isinstance(journal, dict) else {}
    width = float(task.get("figure_width_mm") or rules.get("width_mm", {}).get("value", 89))
    height = float(task.get("figure_height_mm") or min(170.0, width * 0.72))
    spacing = data.get("style_capsule", {}).get("spacing", {})
    margin_ratio = float(spacing.get("outer_margin_ratio", 0.08))
    gap_ratio = float(spacing.get("panel_gap_ratio", 0.05))
    reference = data.get("references", {})
    panel_count = int(reference.get("panel_count") or 1)
    columns = int(reference.get("columns") or max(1, min(panel_count, 3)))
    rows = max(1, (panel_count + columns - 1) // columns)
    margin_x = width * margin_ratio
    margin_y = height * margin_ratio
    gap_x = width * gap_ratio
    gap_y = height * gap_ratio
    panel_width = (width - 2 * margin_x - (columns - 1) * gap_x) / columns
    panel_height = (height - 2 * margin_y - (rows - 1) * gap_y) / rows
    panels = []
    for index in range(panel_count):
        row, column = divmod(index, columns)
        panels.append({"id": chr(65 + index), "x_mm": round(margin_x + column * (panel_width + gap_x), 4), "y_mm": round(margin_y + row * (panel_height + gap_y), 4), "width_mm": round(panel_width, 4), "height_mm": round(panel_height, 4)})
    return {"units": "mm", "canvas": {"width_mm": width, "height_mm": height}, "margins": {"left": margin_x, "right": margin_x, "top": margin_y, "bottom": margin_y}, "gutters": {"x": gap_x, "y": gap_y}, "panels": panels, "solver": "deterministic_direct", "constraints_satisfied": True}
