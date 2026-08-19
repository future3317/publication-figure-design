# -*- coding: utf-8 -*-
"""Unified palette manager for the academic-figure skill.

All plotting functions should obtain categorical colors through this module
instead of scattering hard-coded hex codes. The manager guarantees:

* deterministic color order for a given palette id;
* stable subset colors when ``n`` is no larger than the palette length;
* deterministic extension colors when ``n`` exceeds the palette length;
* user-specified explicit colors always take precedence over palette defaults.

Palettes are qualitative / categorical only. Do not use them as continuous
numerical colormaps.
"""

from __future__ import annotations

import colorsys
import re
from typing import Iterable, List, Optional, Sequence, Tuple

try:
    from .palettes import PALETTES, ZH_TO_ID
except ImportError:  # pragma: no cover - allow standalone import during dev
    from palettes import PALETTES, ZH_TO_ID


__all__ = [
    "contrast_ratio",
    "list_palettes",
    "get_palette_info",
    "get_palette",
    "pick_text_color",
    "extend_palette",
    "resolve_palette",
    "resolve_colors",
    "set_default_palette",
    "preview_palettes",
]


# Module-level default. Changed by ``set_default_palette``.
_default_palette_id: str = "pastel_girl"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_RE_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _is_valid_hex(color: str) -> bool:
    return isinstance(color, str) and _RE_HEX.match(color) is not None


def _normalize_name(name: Optional[str]) -> str:
    """Resolve a palette id or Chinese alias to the canonical id.

    Raises ``ValueError`` with a clear message when the palette is unknown.
    """
    if name is None:
        raise ValueError("palette name cannot be None; use resolve_palette() for default lookup.")

    if name in PALETTES:
        return name

    if name in ZH_TO_ID:
        return ZH_TO_ID[name]

    # Case-insensitive / whitespace-tolerant lookup.
    key = str(name).strip().lower()
    for pid in PALETTES:
        if pid.lower() == key:
            return pid
    for zh, pid in ZH_TO_ID.items():
        if zh.lower() == key:
            return pid

    known = list(PALETTES.keys()) + list(ZH_TO_ID.keys())
    raise ValueError(
        f"Unknown palette name: {name!r}. "
        f"Available palette ids / Chinese aliases: {known}"
    )


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """Convert '#RRGGBB' to normalized RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _linear_channel(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    red, green, blue = (_linear_channel(channel) for channel in _hex_to_rgb(hex_color))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    """Return the WCAG contrast ratio of two ``#RRGGBB`` colors."""
    light, dark = sorted((_relative_luminance(foreground), _relative_luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def pick_text_color(background: str, minimum_ratio: float = 4.5) -> str:
    """Choose dark ink or white text with the strongest readable contrast.

    ``minimum_ratio`` documents the publication-size threshold; the best of
    the two neutral inks is still returned when an unusual background cannot
    meet it, so the rendered QA gate can report the residual failure.
    """
    candidates = ("#222222", "#FFFFFF")
    ratios = {color: contrast_ratio(color, background) for color in candidates}
    return max(candidates, key=ratios.get)


def _rgb_to_hex(rgb: Sequence[float]) -> str:
    """Convert normalized RGB tuple to '#RRGGBB'."""
    return "#" + "".join(f"{max(0, min(255, int(round(c * 255)))):02x}" for c in rgb)


def _interpolate_hex(c1: str, c2: str, t: float) -> str:
    """Interpolate between two hex colors in HSL space (shortest hue path)."""
    h1, l1, s1 = colorsys.rgb_to_hls(*_hex_to_rgb(c1))
    h2, l2, s2 = colorsys.rgb_to_hls(*_hex_to_rgb(c2))

    dh = h2 - h1
    if dh > 0.5:
        dh -= 1.0
    elif dh < -0.5:
        dh += 1.0

    h = (h1 + t * dh) % 1.0
    l = l1 + t * (l2 - l1)
    s = s1 + t * (s2 - s1)
    return _rgb_to_hex(colorsys.hls_to_rgb(h, l, s))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_palettes() -> List[dict]:
    """Return metadata for all built-in palettes.

    Each entry contains ``id``, ``name_zh`` and ``tags``.
    """
    return [
        {"id": pid, "name_zh": info["name_zh"], "tags": list(info["tags"])}
        for pid, info in PALETTES.items()
    ]


def get_palette_info(name: str) -> dict:
    """Return full metadata dict for a palette."""
    pid = _normalize_name(name)
    return dict(PALETTES[pid])


def get_palette(name: str, n: Optional[int] = None) -> List[str]:
    """Return a list of hex colors for the requested palette.

    Parameters
    ----------
    name : str
        Palette id (e.g. ``"summer_beach"``) or Chinese name
        (e.g. ``"夏日海滩"``).
    n : int, optional
        Number of colors requested. If ``None``, all 8 built-in colors are
        returned. If ``n`` is larger than the palette length, ``extend_palette``
        is called automatically.

    Returns
    -------
    List[str]
        Deterministic list of hex colors.
    """
    pid = _normalize_name(name)
    colors = list(PALETTES[pid]["colors"])

    if n is None:
        return colors

    if not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    if n == 0:
        return []
    if n <= len(colors):
        return colors[:n]

    return extend_palette(pid, n)


def extend_palette(name: str, n: int) -> List[str]:
    """Extend a palette to ``n`` colors while preserving the original 8 colors.

    Additional colors are generated by evenly sampling the closed loop of
    base colors in HSL space. The original 8 colors are kept unchanged at the
    front of the returned list; supplementary colors are appended afterwards.

    Parameters
    ----------
    name : str
        Palette id or Chinese alias.
    n : int
        Total number of colors needed (must be > 0).

    Returns
    -------
    List[str]
        ``n`` colors: the original palette in order, followed by generated
        supplementary colors.
    """
    pid = _normalize_name(name)
    base = list(PALETTES[pid]["colors"])
    m = len(base)

    if not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if n <= m:
        return base[:n]

    extra = n - m

    # Generate ``extra`` supplementary colors by evenly sampling the closed
    # loop of base colors in HSL space. The original 8 colors are appended
    # unchanged at the front; extras are appended deterministically afterwards.
    extras: List[str] = []
    for j in range(1, extra + 1):
        pos = j * m / (extra + 1)
        i = int(pos) % m
        t = pos - int(pos)
        extras.append(_interpolate_hex(base[i], base[(i + 1) % m], t))

    return base + extras


def resolve_palette(name: Optional[str] = None, n: Optional[int] = None) -> List[str]:
    """Resolve a palette name to colors, falling back to the skill default.

    This is the function plotting utilities should call internally when the
    user has not supplied explicit colors.

    Parameters
    ----------
    name : str, optional
        Palette id or Chinese alias. If ``None``, the skill default palette is
        used.
    n : int, optional
        Number of colors requested.

    Returns
    -------
    List[str]
        Deterministic list of hex colors.
    """
    global _default_palette_id
    if name is None:
        name = _default_palette_id
    return get_palette(name, n)


def resolve_colors(
    colors: Optional[Sequence[str]] = None,
    palette: Optional[str] = None,
    n: Optional[int] = None,
) -> List[str]:
    """Resolve final colors with the priority: explicit > palette > default.

    Parameters
    ----------
    colors : sequence of str, optional
        Explicit user-supplied colors. Returned as-is when provided.
    palette : str, optional
        Palette id or Chinese alias. Falls back to the skill default when
        ``None``.
    n : int, optional
        Number of colors needed. Ignored when ``colors`` is provided.

    Returns
    -------
    List[str]
        Final color list.
    """
    if colors is not None:
        return list(colors)
    return resolve_palette(palette, n)


def set_default_palette(name: str) -> None:
    """Set the skill-wide default palette for the current task/session.

    Parameters
    ----------
    name : str
        Palette id or Chinese alias.
    """
    global _default_palette_id
    _default_palette_id = _normalize_name(name)


def preview_palettes(
    names: Optional[Sequence[str]] = None,
    n: Optional[int] = None,
    swatch_width: float = 0.8,
    swatch_height: float = 0.4,
    figsize: Optional[Tuple[float, float]] = None,
    font: Optional[str] = None,
) -> object:
    """Render a matplotlib figure showing color swatches for built-in palettes.

    Parameters
    ----------
    names : sequence of str, optional
        Palette ids or Chinese aliases to display. Defaults to all palettes.
    n : int, optional
        Number of colors to render per palette. Defaults to the full palette.
    swatch_width : float
        Horizontal size of one color swatch (inches).
    swatch_height : float
        Vertical size of one palette row (inches).
    figsize : tuple of float, optional
        Override figure size. If ``None``, size is computed automatically.
    font : str, optional
        Font family name for Chinese labels (e.g. ``"SimHei"``, ``"Arial Unicode MS"``).
        Uses matplotlib default if not specified.

    Returns
    -------
    matplotlib.figure.Figure
        A figure containing color swatches with labels.
    """
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import Rectangle

    if names is None:
        names = list(PALETTES.keys())
    else:
        names = list(names)

    rows = []
    max_len = 0
    for raw_name in names:
        pid = _normalize_name(raw_name)
        info = PALETTES[pid]
        colors = get_palette(pid, n)
        rows.append((info["name_zh"], pid, colors))
        max_len = max(max_len, len(colors))

    if figsize is None:
        figsize = (
            max(4.0, max_len * swatch_width + 2.0),
            max(2.0, len(rows) * swatch_height + 0.5),
        )

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, max_len * swatch_width + 0.2)
    ax.set_ylim(0, len(rows) * swatch_height)
    ax.invert_yaxis()
    ax.axis("off")

    label_font = FontProperties(family=font) if font else None

    for row_idx, (zh_name, pid, colors) in enumerate(rows):
        y = row_idx * swatch_height
        ax.text(
            0.05,
            y + swatch_height / 2,
            f"{zh_name}\n({pid})",
            va="center",
            ha="left",
            fontsize=8,
            transform=ax.transData,
            fontproperties=label_font,
        )
        x_offset = 1.6
        for col_idx, color in enumerate(colors):
            rect = Rectangle(
                (x_offset + col_idx * swatch_width, y + 0.05),
                swatch_width * 0.9,
                swatch_height * 0.75,
                facecolor=color,
                edgecolor="#333333",
                linewidth=0.5,
            )
            ax.add_patch(rect)
            ax.text(
                x_offset + col_idx * swatch_width + swatch_width * 0.45,
                y + swatch_height * 0.82,
                color,
                ha="center",
                va="bottom",
                fontsize=5,
                color="#333333",
            )

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Validation helper (useful for QA / tests)
# ---------------------------------------------------------------------------

def validate_palettes() -> Tuple[bool, List[str]]:
    """Validate all built-in palettes.

    Returns a tuple ``(ok, errors)``. ``ok`` is True when every palette has
    exactly 8 valid hex colors and required metadata fields.
    """
    errors: List[str] = []
    required = {"id", "name_zh", "colors", "tags", "type", "source"}
    for pid, info in PALETTES.items():
        missing = required - set(info.keys())
        if missing:
            errors.append(f"Palette {pid!r} missing fields: {sorted(missing)}")
            continue
        if info["id"] != pid:
            errors.append(f"Palette {pid!r}: id mismatch ({info['id']!r})")
        if info["type"] != "categorical":
            errors.append(f"Palette {pid!r}: type is not 'categorical'")
        colors = info["colors"]
        if len(colors) != 8:
            errors.append(f"Palette {pid!r}: expected 8 colors, got {len(colors)}")
        for c in colors:
            if not _is_valid_hex(c):
                errors.append(f"Palette {pid!r}: invalid hex color {c!r}")
    return len(errors) == 0, errors
