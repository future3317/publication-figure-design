"""Simple mm/pt layout primitives used by the design compiler."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Box:
    id: str
    x_mm: float = 0.0
    y_mm: float = 0.0
    width_mm: float = 0.0
    height_mm: float = 0.0
    constraints: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Canvas(Box):
    pass


class PanelBox(Box):
    pass


class PlotBox(Box):
    pass


class LegendBox(Box):
    pass


class ColorbarBox(Box):
    pass


class TextBox(Box):
    pass


class AnnotationBox(Box):
    pass


@dataclass
class Gutter:
    id: str
    size_mm: float
    axis: str = "x"


@dataclass
class Margin:
    id: str
    size_mm: float
    side: str


@dataclass
class AlignmentGuide:
    id: str
    axis: str
    position_mm: float
