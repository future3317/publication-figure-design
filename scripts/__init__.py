# -*- coding: utf-8 -*-
"""Academic figure skill utility scripts."""

from .palette_manager import (
    extend_palette,
    get_palette,
    get_palette_info,
    list_palettes,
    preview_palettes,
    resolve_colors,
    resolve_palette,
    set_default_palette,
    validate_palettes,
)
from .reference_library import (
    REFERENCE_METADATA_FIELDS,
    ReferenceLibrary,
    VisualReference,
    archive_generated_figure,
    ingest_image,
    resolve_visual_style,
)

__all__ = [
    "extend_palette",
    "get_palette",
    "get_palette_info",
    "list_palettes",
    "preview_palettes",
    "resolve_colors",
    "resolve_palette",
    "set_default_palette",
    "validate_palettes",
    "REFERENCE_METADATA_FIELDS",
    "ReferenceLibrary",
    "VisualReference",
    "archive_generated_figure",
    "ingest_image",
    "resolve_visual_style",
]
