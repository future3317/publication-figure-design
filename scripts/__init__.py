# -*- coding: utf-8 -*-
"""Academic figure skill utility scripts."""

from .palette_manager import (
    contrast_ratio,
    extend_palette,
    get_palette,
    get_palette_info,
    list_palettes,
    pick_text_color,
    preview_palettes,
    resolve_colors,
    resolve_palette,
    set_default_palette,
    validate_palettes,
)
from .production_asset_manager import (
    PRODUCTION_METADATA_FIELDS,
    ProductionAsset,
    ProductionAssetLibrary,
)
from .reference_library import (
    REFERENCE_METADATA_FIELDS,
    ReferenceLibrary,
    VisualReference,
    archive_generated_figure,
    ingest_image,
    resolve_visual_style,
    normalize_figure_type,
)

__all__ = [
    "contrast_ratio",
    "extend_palette",
    "get_palette",
    "get_palette_info",
    "list_palettes",
    "pick_text_color",
    "preview_palettes",
    "resolve_colors",
    "resolve_palette",
    "set_default_palette",
    "validate_palettes",
    "PRODUCTION_METADATA_FIELDS",
    "ProductionAsset",
    "ProductionAssetLibrary",
    "REFERENCE_METADATA_FIELDS",
    "ReferenceLibrary",
    "VisualReference",
    "archive_generated_figure",
    "ingest_image",
    "resolve_visual_style",
    "normalize_figure_type",
]
