"""Renderer contract shared by the package runtime and script adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REQUIRED_SPECS = ("TypographySpec", "PaletteSpec", "LayoutSpec", "ComponentSpec")


def validate_render_contract(render_plan: Mapping[str, Any], *, reference_led: bool) -> tuple[bool, list[str]]:
    if not reference_led:
        return True, []
    consumed = render_plan.get("consumed_specs")
    failures: list[str] = []
    if not isinstance(consumed, (list, tuple, set)):
        failures.append("reference-led render must declare consumed_specs")
        consumed = []
    missing = [name for name in REQUIRED_SPECS if name not in consumed]
    if missing:
        failures.append("renderer did not consume: " + ", ".join(missing))
    if render_plan.get("default_overrides_spec") is True:
        failures.append("renderer cannot override StyleSpec with backend defaults")
    if not render_plan.get("style_spec_version"):
        failures.append("reference-led render must record style_spec_version")
    return not failures, failures


def strict_renderer_payload(style_spec: Mapping[str, Any], layout_spec: Mapping[str, Any], component_spec: Mapping[str, Any], typography_spec: Mapping[str, Any], palette_spec: Mapping[str, Any], *, renderer_version: str) -> dict[str, Any]:
    return {
        "style_spec_version": str(style_spec.get("schema_version", "1.0")),
        "renderer_version": renderer_version,
        "TypographySpec": dict(typography_spec),
        "PaletteSpec": dict(palette_spec),
        "LayoutSpec": dict(layout_spec),
        "ComponentSpec": dict(component_spec),
        "default_overrides_spec": False,
        "consumed_specs": list(REQUIRED_SPECS),
    }
