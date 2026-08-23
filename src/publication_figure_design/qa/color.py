"""Palette contrast, CVD and grayscale QA."""

from __future__ import annotations

from typing import Any, Mapping


def check_palette(palette: Mapping[str, Any], *, background: str = "#FFFFFF") -> dict[str, Any]:
    roles = dict(palette.get("roles", palette.get("semantic_roles", {})))
    return {"passed": bool(roles), "role_count": len(roles), "background": background, "cvd": palette.get("cvd_score"), "grayscale": palette.get("grayscale_score"), "contrast": palette.get("contrast", {})}
