"""Small, serialisable contracts used between workflow stages.

The contracts deliberately use plain JSON-compatible values.  A renderer or
an existing script can therefore consume them without importing this package.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Mapping, Type, TypeVar


SCHEMA_VERSION = "1.0"
T = TypeVar("T", bound="Contract")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value


@dataclass
class Contract:
    """Base class with a versioned JSON representation."""

    schema_version: str = SCHEMA_VERSION
    contract_name: ClassVar[str] = "Contract"

    def to_dict(self) -> Dict[str, Any]:
        result = _jsonable(asdict(self))
        result["contract_name"] = self.contract_name
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, Any]) -> T:
        expected = data.get("schema_version", SCHEMA_VERSION)
        if expected != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported {cls.__name__} schema_version {expected!r}; "
                f"expected {SCHEMA_VERSION!r}"
            )
        known = {field.name for field in fields(cls)}
        unknown = set(data) - known - {"contract_name"}
        if unknown:
            raise ValueError(f"Unknown {cls.__name__} fields: {sorted(unknown)}")
        return cls(**{key: data[key] for key in known if key in data})


@dataclass
class TaskSpec(Contract):
    task_id: str = ""
    mode: str = "create"
    objective: str = ""
    requested_outputs: List[str] = None  # type: ignore[assignment]
    metadata: Dict[str, Any] = None  # type: ignore[assignment]
    contract_name: ClassVar[str] = "TaskSpec"

    def __post_init__(self) -> None:
        if self.requested_outputs is None:
            self.requested_outputs = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SourceSpec(Contract):
    source_id: str = ""
    scientific_question: str = ""
    data_paths: List[str] = None  # type: ignore[assignment]
    code_paths: List[str] = None  # type: ignore[assignment]
    figure_paths: List[str] = None  # type: ignore[assignment]
    variable_roles: Dict[str, str] = None  # type: ignore[assignment]
    uncertainty: Dict[str, Any] = None  # type: ignore[assignment]
    provenance: Dict[str, Any] = None  # type: ignore[assignment]
    contract_name: ClassVar[str] = "SourceSpec"

    def __post_init__(self) -> None:
        for name in ("data_paths", "code_paths", "figure_paths"):
            if getattr(self, name) is None:
                setattr(self, name, [])
        for name in ("variable_roles", "uncertainty", "provenance"):
            if getattr(self, name) is None:
                setattr(self, name, {})


@dataclass
class TargetSpec(Contract):
    journal: str = ""
    column_width_mm: float = 0.0
    figure_width_mm: float = 0.0
    figure_height_mm: float = 0.0
    dpi: int = 300
    vector_format: str = "pdf"
    raster_format: str = "png"
    min_font_pt: float = 5.0
    font_family: str = ""
    journal_profile: Dict[str, Any] = None  # type: ignore[assignment]
    contract_name: ClassVar[str] = "TargetSpec"

    def __post_init__(self) -> None:
        if self.journal_profile is None:
            self.journal_profile = {}


@dataclass
class ReferenceSet(Contract):
    structure_reference: str = ""
    style_reference: str = ""
    component_references: List[str] = None  # type: ignore[assignment]
    annotation_reference: str = ""
    palette_reference: str = ""
    candidates: List[Dict[str, Any]] = None  # type: ignore[assignment]
    selection_reason: str = ""
    contract_name: ClassVar[str] = "ReferenceSet"

    def __post_init__(self) -> None:
        if self.component_references is None:
            self.component_references = []
        if self.candidates is None:
            self.candidates = []


@dataclass
class LayoutSpec(Contract):
    panel_topology: str = "single_panel"
    panel_bboxes: List[Dict[str, float]] = None  # type: ignore[assignment]
    reading_order: List[str] = None  # type: ignore[assignment]
    plot_bboxes: List[Dict[str, float]] = None  # type: ignore[assignment]
    legend_bboxes: List[Dict[str, float]] = None  # type: ignore[assignment]
    whitespace_map: Dict[str, Any] = None  # type: ignore[assignment]
    panel_gaps: Dict[str, float] = None  # type: ignore[assignment]
    contract_name: ClassVar[str] = "LayoutSpec"

    def __post_init__(self) -> None:
        for name in ("panel_bboxes", "reading_order", "plot_bboxes", "legend_bboxes"):
            if getattr(self, name) is None:
                setattr(self, name, [])
        for name in ("whitespace_map", "panel_gaps"):
            if getattr(self, name) is None:
                setattr(self, name, {})


@dataclass
class StyleSpec(Contract):
    canvas_background: str = ""
    panel_background: str = ""
    palette_roles: Dict[str, str] = None  # type: ignore[assignment]
    palette_oklch: Dict[str, List[float]] = None  # type: ignore[assignment]
    font_family: str = ""
    font_sizes: Dict[str, float] = None  # type: ignore[assignment]
    font_weights: Dict[str, str] = None  # type: ignore[assignment]
    line_height: float = 1.0
    stroke_widths: Dict[str, float] = None  # type: ignore[assignment]
    marker: Dict[str, Any] = None  # type: ignore[assignment]
    opacity: Dict[str, float] = None  # type: ignore[assignment]
    grid_rules: Dict[str, Any] = None  # type: ignore[assignment]
    spine_rules: Dict[str, Any] = None  # type: ignore[assignment]
    tick_rules: Dict[str, Any] = None  # type: ignore[assignment]
    legend_geometry: Dict[str, Any] = None  # type: ignore[assignment]
    corner_radius: float = 0.0
    annotation_style: Dict[str, Any] = None  # type: ignore[assignment]
    panel_gaps: Dict[str, float] = None  # type: ignore[assignment]
    whitespace_rhythm: Dict[str, Any] = None  # type: ignore[assignment]
    information_density: str = ""
    axis_treatment: Dict[str, Any] = None  # type: ignore[assignment]
    contract_name: ClassVar[str] = "StyleSpec"

    def __post_init__(self) -> None:
        for name in (
            "palette_roles", "palette_oklch", "font_sizes", "font_weights",
            "stroke_widths", "marker", "opacity", "grid_rules", "spine_rules",
            "tick_rules", "legend_geometry", "annotation_style", "panel_gaps",
            "whitespace_rhythm", "axis_treatment",
        ):
            if getattr(self, name) is None:
                setattr(self, name, {})


@dataclass
class TypographySpec(Contract):
    """Resolved typography tokens compiled from a reference or target journal."""

    font_family: str = ""
    roles: Dict[str, Dict[str, Any]] = None  # type: ignore[assignment]
    fallback_chain: List[str] = None  # type: ignore[assignment]
    measured_font: str = ""
    contract_name: ClassVar[str] = "TypographySpec"

    def __post_init__(self) -> None:
        if self.roles is None:
            self.roles = {}
        if self.fallback_chain is None:
            self.fallback_chain = []


@dataclass
class PaletteSpec(Contract):
    """Semantic palette roles plus measured contrast/accessibility evidence."""

    roles: Dict[str, str] = None  # type: ignore[assignment]
    lab: Dict[str, List[float]] = None  # type: ignore[assignment]
    contrast: Dict[str, float] = None  # type: ignore[assignment]
    colorblind_safe: bool = False
    contract_name: ClassVar[str] = "PaletteSpec"

    def __post_init__(self) -> None:
        if self.roles is None:
            self.roles = {}
        if self.lab is None:
            self.lab = {}
        if self.contrast is None:
            self.contrast = {}


@dataclass
class ComponentSpec(Contract):
    """Geometry and rendering tokens for arrows, marks, legends, and annotations."""

    components: Dict[str, Dict[str, Any]] = None  # type: ignore[assignment]
    crops: List[Dict[str, Any]] = None  # type: ignore[assignment]
    contract_name: ClassVar[str] = "ComponentSpec"

    def __post_init__(self) -> None:
        if self.components is None:
            self.components = {}
        if self.crops is None:
            self.crops = []


@dataclass
class BindingMap(Contract):
    bindings: Dict[str, Dict[str, Any]] = None  # type: ignore[assignment]
    unresolved_orphan_series: List[str] = None  # type: ignore[assignment]
    contract_name: ClassVar[str] = "BindingMap"

    def __post_init__(self) -> None:
        if self.bindings is None:
            self.bindings = {}
        if self.unresolved_orphan_series is None:
            self.unresolved_orphan_series = []


@dataclass
class RenderPlan(Contract):
    panel_renderers: Dict[str, str] = None  # type: ignore[assignment]
    assembler: str = ""
    backend: str = ""
    vector_format: str = "pdf"
    raster_format: str = "png"
    dpi: int = 300
    font_fallback: str = ""
    variants: int = 1
    contract_name: ClassVar[str] = "RenderPlan"

    def __post_init__(self) -> None:
        if self.panel_renderers is None:
            self.panel_renderers = {}


@dataclass
class QAReport(Contract):
    scientific: Dict[str, Any] = None  # type: ignore[assignment]
    statistics: Dict[str, Any] = None  # type: ignore[assignment]
    layout: Dict[str, Any] = None  # type: ignore[assignment]
    typography: Dict[str, Any] = None  # type: ignore[assignment]
    color: Dict[str, Any] = None  # type: ignore[assignment]
    reference_fidelity: Dict[str, Any] = None  # type: ignore[assignment]
    accessibility: Dict[str, Any] = None  # type: ignore[assignment]
    export: Dict[str, Any] = None  # type: ignore[assignment]
    passed: bool = False
    score: float = 0.0
    issues: List[str] = None  # type: ignore[assignment]
    metrics: Dict[str, float] = None  # type: ignore[assignment]
    contract_name: ClassVar[str] = "QAReport"

    def __post_init__(self) -> None:
        for name in (
            "scientific", "statistics", "layout", "typography", "color",
            "reference_fidelity", "accessibility", "export", "metrics",
        ):
            if getattr(self, name) is None:
                setattr(self, name, {})
        if self.issues is None:
            self.issues = []


@dataclass
class ExportManifest(Contract):
    task_id: str = ""
    figure_path: str = ""
    source_paths: List[str] = None  # type: ignore[assignment]
    qa_report_path: str = ""
    reference_provenance: Dict[str, Any] = None  # type: ignore[assignment]
    formats: List[str] = None  # type: ignore[assignment]
    font_used: str = ""
    font_substitution_policy: str = "record_actual_font_and_warn"
    metadata: Dict[str, Any] = None  # type: ignore[assignment]
    contract_name: ClassVar[str] = "ExportManifest"

    def __post_init__(self) -> None:
        if self.source_paths is None:
            self.source_paths = []
        if self.reference_provenance is None:
            self.reference_provenance = {}
        if self.formats is None:
            self.formats = []
        if self.metadata is None:
            self.metadata = {}
