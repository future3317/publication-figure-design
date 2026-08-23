"""Constraint helpers with required/strong/medium/weak priority labels."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


def required_constraints(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    constraints = list(packet.get("layout_constraints", []))
    return [constraint for constraint in constraints if str(constraint.get("priority", "required")) == "required"]


def check_constraints(layout: Mapping[str, Any], constraints: Iterable[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    for constraint in constraints:
        path = str(constraint.get("path", ""))
        value: Any = layout
        for key in path.split("."):
            if not isinstance(value, Mapping) or key not in value:
                failures.append(f"missing layout value for {path}")
                value = None
                break
            value = value[key]
        if value is None:
            continue
        operator = constraint.get("operator", "==")
        expected = constraint.get("value")
        if operator == ">=" and value < expected:
            failures.append(f"{path}={value} below {expected}")
        elif operator == "<=" and value > expected:
            failures.append(f"{path}={value} above {expected}")
        elif operator == "==" and value != expected:
            failures.append(f"{path}={value} does not equal {expected}")
    return failures
