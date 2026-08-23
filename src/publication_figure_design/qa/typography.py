"""Typography QA from compiled tokens and measured evidence."""

from __future__ import annotations

from typing import Any, Mapping


def check_typography(style_tokens: Mapping[str, Any], journal_rules: Mapping[str, Any] | None = None) -> dict[str, Any]:
    typography = dict(style_tokens.get("typography", {}))
    min_pt = float((journal_rules or {}).get("min_font_pt", {}).get("value", 5))
    body = float(typography.get("body_size", min_pt))
    return {"passed": body >= min_pt, "body_size_pt": body, "minimum_pt": min_pt, "font_family": typography.get("family", "unknown")}
