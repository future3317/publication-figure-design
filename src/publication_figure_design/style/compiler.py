"""Compile a reference-derived style contract into renderer settings.

The compiler deliberately has no journal-specific defaults beyond a small,
neutral fallback.  A supplied :class:`StyleSpec` is the source of truth; a
renderer may only fill missing optional fields from ``StyleSpec.fallback()``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence


def _merge(base: Dict[str, Any], value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        base.update(dict(value))
    return base


def _coerce_style(value: Any) -> "StyleSpec":
    if isinstance(value, StyleSpec):
        return value
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        raise TypeError("style must be a StyleSpec, mapping, or contract with to_dict()")
    # Adapt the orchestration contract's flat names to this renderer-facing
    # nested representation. Both remain valid JSON artifacts; this bridge is
    # intentionally one-way so there is still one design contract.
    value = dict(value)
    if "canvas_background" in value:
        value.setdefault("canvas", {"background": value["canvas_background"]})
    if "panel_background" in value:
        value.setdefault("panel", {"background": value["panel_background"]})
    if "palette_roles" in value:
        value.setdefault("palette", {"roles": value["palette_roles"]})
    if "font_family" in value or "font_sizes" in value or "font_weights" in value:
        value.setdefault("typography", {})
        value["typography"].setdefault("family", value.get("font_family"))
        sizes = value.get("font_sizes", {}) or {}
        value["typography"].setdefault("title_size", sizes.get("title"))
        value["typography"].setdefault("body_size", sizes.get("body", sizes.get("base")))
        value["typography"].setdefault("tick_size", sizes.get("tick"))
        value["typography"].setdefault("annotation_size", sizes.get("annotation"))
        value["typography"].setdefault("weights", value.get("font_weights", {}))
        if value.get("line_height") is not None:
            value["typography"].setdefault("line_height", value["line_height"])
    for old, new in (("grid_rules", "grid"), ("spine_rules", "spine"), ("tick_rules", "ticks"), ("legend_geometry", "legend"), ("annotation_style", "annotation"), ("panel_gaps", "spacing")):
        if old in value:
            value.setdefault(new, value[old])
    if "information_density" in value:
        value.setdefault("density", {"level": value["information_density"]})
    if "axis_treatment" in value:
        value.setdefault("axis", value["axis_treatment"])
    return StyleSpec.from_dict(value)


@dataclass
class StyleSpec:
    """Machine-readable visual language shared by every renderer.

    Nested dictionaries are intentional: they keep roles explicit and allow
    image, SVG, and matplotlib backends to consume the same contract without
    inventing backend-specific design decisions.
    """

    schema_version: str = "1.0"
    canvas: Dict[str, Any] = field(default_factory=lambda: {"background": "#FFFFFF", "aspect_ratio": 1.6})
    panel: Dict[str, Any] = field(default_factory=lambda: {"background": "#FFFFFF", "corner_radius": 0})
    palette: Dict[str, Any] = field(default_factory=lambda: {"roles": {}, "colors": []})
    typography: Dict[str, Any] = field(default_factory=lambda: {
        "family": "DejaVu Sans", "title_size": 12, "body_size": 9,
        "tick_size": 8, "annotation_size": 8, "relative_sizes": {"title": 1.35, "body": 1.0, "tick": 0.9, "annotation": 0.9},
        "weights": {"title": 600, "body": 400, "tick": 400, "annotation": 500},
        "line_height": 1.15,
    })
    strokes: Dict[str, Any] = field(default_factory=lambda: {"axis": 0.8, "grid": 0.5, "line": 1.5, "annotation": 0.8, "outline": 0.8})
    markers: Dict[str, Any] = field(default_factory=lambda: {"shape": "o", "size": 4, "edge_width": 0.6})
    opacity: Dict[str, Any] = field(default_factory=lambda: {"fill": 0.85, "line": 1.0, "grid": 0.35, "annotation": 1.0})
    grid: Dict[str, Any] = field(default_factory=lambda: {"visible": False, "color": "#D9DEE7", "linestyle": "-", "axis": "y"})
    spine: Dict[str, Any] = field(default_factory=lambda: {"visible": True, "color": "#1F2933", "width": 0.8, "top": False, "right": False})
    ticks: Dict[str, Any] = field(default_factory=lambda: {"direction": "out", "length": 3, "width": 0.8, "color": "#1F2933"})
    legend: Dict[str, Any] = field(default_factory=lambda: {"loc": "best", "frame": False, "fontsize": 8, "ncol": 1, "handlelength": 1.5})
    annotation: Dict[str, Any] = field(default_factory=lambda: {"color": "#1F2933", "arrowstyle": "->", "arrow_color": "#1F2933", "box": False, "box_radius": 0})
    spacing: Dict[str, Any] = field(default_factory=lambda: {"left": 0.12, "right": 0.96, "bottom": 0.12, "top": 0.94, "panel_gap": 0.08, "label_pad": 3})
    density: Dict[str, Any] = field(default_factory=lambda: {"level": "moderate", "marks_per_panel": None, "whitespace_ratio": 0.25})
    axis: Dict[str, Any] = field(default_factory=lambda: {"label_weight": 500, "label_size": 9, "zero_baseline": False, "scale": "linear"})

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "StyleSpec":
        """Build a spec while preserving unknown top-level extensions."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        aliases = {
            "background": "canvas", "fonts": "typography", "stroke_widths": "strokes",
            "marker": "markers", "annotation_style": "annotation", "spacing_rhythm": "spacing",
        }
        normalized = dict(value)
        for old, new in aliases.items():
            if old in normalized and new not in normalized:
                normalized[new] = normalized[old]
        kwargs = {k: v for k, v in normalized.items() if k in known}
        # Accept common sidecar aliases without making the sidecar less clear.
        if "background" in value and "canvas" not in kwargs:
            kwargs["canvas"] = {"background": value["background"]}
        base = cls()
        # Sidecars commonly provide only a few style tokens. Merge them into
        # the neutral contract so a missing optional token never becomes a
        # backend's undocumented default.
        for key, item in kwargs.items():
            if isinstance(item, Mapping) and isinstance(getattr(base, key, None), Mapping):
                merged = dict(getattr(base, key))
                merged.update(item)
                kwargs[key] = merged
        spec = cls(**kwargs)
        for key, val in value.items():
            if key not in known:
                setattr(spec, key, val)
        return spec

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def fallback(cls) -> "StyleSpec":
        return cls()

    def color(self, role: str, default: str = "#1F2933") -> str:
        roles = self.palette.get("roles", {}) if isinstance(self.palette, Mapping) else {}
        value = roles.get(role, self.palette.get(role) if isinstance(self.palette, Mapping) else None)
        return str(value or default)

    # Read-only aliases make common sidecar vocabulary discoverable without
    # duplicating the underlying source of truth.
    @property
    def background(self) -> str:
        return str(self.canvas.get("background", "#FFFFFF"))

    @property
    def fonts(self) -> Dict[str, Any]:
        return self.typography

    @property
    def relative_sizes(self) -> Dict[str, Any]:
        return dict(self.typography.get("relative_sizes", {}))

    @property
    def weights(self) -> Dict[str, Any]:
        return dict(self.typography.get("weights", {}))


def apply_style_spec_matplotlib(spec: StyleSpec | Mapping[str, Any], *, rc: Optional[MutableMapping[str, Any]] = None) -> MutableMapping[str, Any]:
    """Apply the contract to matplotlib rcParams and return the mapping.

    Importing matplotlib is deferred so the style compiler remains usable by
    SVG-only and image-generation workflows.
    """
    style = _coerce_style(spec)
    if rc is None:
        try:
            import matplotlib as mpl
            rc = mpl.rcParams
        except ImportError:  # pragma: no cover - SVG-only installations
            rc = {}
    typo, stroke, grid, spine, ticks, legend = style.typography, style.strokes, style.grid, style.spine, style.ticks, style.legend
    values = {
        "font.family": typo.get("family"), "font.size": typo.get("body_size"),
        "axes.titlesize": typo.get("title_size"), "axes.labelsize": style.axis.get("label_size", typo.get("body_size")),
        "xtick.labelsize": typo.get("tick_size"), "ytick.labelsize": typo.get("tick_size"),
        "axes.linewidth": stroke.get("axis"), "grid.linewidth": stroke.get("grid"),
        "grid.color": grid.get("color"), "grid.alpha": style.opacity.get("grid"), "grid.linestyle": grid.get("linestyle"),
        "xtick.direction": ticks.get("direction"), "ytick.direction": ticks.get("direction"),
        "xtick.major.size": ticks.get("length"), "ytick.major.size": ticks.get("length"),
        "xtick.major.width": ticks.get("width"), "ytick.major.width": ticks.get("width"),
        "axes.facecolor": style.panel.get("background"), "figure.facecolor": style.canvas.get("background"),
        "legend.fontsize": legend.get("fontsize"), "legend.frameon": legend.get("frame", False),
    }
    for key, value in values.items():
        if value is None:
            continue
        try:
            rc[key] = value
        except (KeyError, ValueError):
            # A custom mapping used by a caller may not expose every
            # matplotlib token; silently skip only tokens its backend cannot
            # represent.
            continue
    return rc


def apply_style_spec_svg(spec: StyleSpec | Mapping[str, Any]) -> Dict[str, Any]:
    """Return SVG-friendly CSS tokens derived solely from ``StyleSpec``."""
    style = _coerce_style(spec)
    typo, stroke = style.typography, style.strokes
    return {
        "canvas_background": style.canvas.get("background"), "panel_background": style.panel.get("background"),
        "font_family": typo.get("family"), "font_size": typo.get("body_size"),
        "title_size": typo.get("title_size"), "tick_size": typo.get("tick_size"), "annotation_size": typo.get("annotation_size"),
        "axis_stroke_width": stroke.get("axis"), "grid_stroke_width": stroke.get("grid"),
        "line_stroke_width": stroke.get("line"), "annotation_stroke_width": stroke.get("annotation"),
        "palette_roles": dict(style.palette.get("roles", {})), "opacity": dict(style.opacity),
        "legend": dict(style.legend), "spacing": dict(style.spacing), "axis": dict(style.axis),
    }


def build_image_generation_style_prompt(spec: StyleSpec | Mapping[str, Any], *, purpose: str = "scientific figure") -> str:
    """Make an explicit, non-ambiguous style prompt for image panels."""
    style = _coerce_style(spec)
    roles = ", ".join(f"{k}={v}" for k, v in style.palette.get("roles", {}).items())
    return (
        f"Create a publication-grade {purpose}. Use the supplied style contract exactly: "
        f"background {style.canvas.get('background')}, panel {style.panel.get('background')}; "
        f"font {style.typography.get('family')}, title/body/tick sizes "
        f"{style.typography.get('title_size')}/{style.typography.get('body_size')}/{style.typography.get('tick_size')} pt, "
        f"weights {style.typography.get('weights')}; palette roles [{roles}]; "
        f"stroke widths {style.strokes}; marker {style.markers.get('shape')} size {style.markers.get('size')}; "
        f"opacity {style.opacity}; grid {style.grid}; spine {style.spine}; "
        f"legend geometry {style.legend}; annotations {style.annotation}; spacing {style.spacing}; "
        f"information density {style.density.get('level')}. Preserve whitespace rhythm and axis treatment."
    )
