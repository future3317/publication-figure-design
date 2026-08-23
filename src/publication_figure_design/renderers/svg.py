"""SVG utility functions that preserve editable text and source metadata."""

from __future__ import annotations

from pathlib import Path


def read_svg(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def wrap_svg(content: str, *, width_mm: float, height_mm: float, panel_id: str) -> str:
    return f'<g id="panel-{panel_id}" data-panel-id="{panel_id}">{content}</g>'
