"""Lightweight SVG analyzer; exact coordinates are retained when present."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping

from ..dna import ReferenceDNA


def analyze_svg(path: Path, *, metadata: Mapping[str, Any] | None = None) -> ReferenceDNA:
    root = ET.parse(path).getroot()
    text_nodes = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "text"]
    paths = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] in {"path", "line", "rect", "circle", "polyline", "polygon"}]
    families: set[str] = set()
    sizes: list[float] = []
    fills: list[str] = []
    for node in text_nodes:
        style = str(node.attrib.get("style", ""))
        family = node.attrib.get("font-family") or re.search(r"font-family:([^;]+)", style)
        if family:
            families.add(str(family.group(1) if hasattr(family, "group") else family).strip())
        size = node.attrib.get("font-size") or re.search(r"font-size:([0-9.]+)", style)
        if size:
            try:
                sizes.append(float(size.group(1) if hasattr(size, "group") else size))
            except ValueError:
                pass
    for node in paths:
        fill = node.attrib.get("fill")
        if fill and fill not in {"none", "transparent"}:
            fills.append(fill)
    meta = dict(metadata or {})
    meta.setdefault("reference_kind", "svg")
    dna = ReferenceDNA.from_metadata(meta)
    dna.identity["source_kind"] = "svg"
    dna.typography.update({"family_class": sorted(families)[0] if families else "sans_serif_unknown", "exact_font": sorted(families), "sizes_pt": sizes, "exactness": "vector_exact"})
    dna.geometry.update({"element_count": len(paths), "fill_tokens": sorted(set(fills))})
    dna.confidence.update({"typography": 0.98, "geometry": 0.96})
    dna.extensions["svg"] = {"width": root.attrib.get("width"), "height": root.attrib.get("height"), "viewBox": root.attrib.get("viewBox"), "text_count": len(text_nodes), "graphic_count": len(paths)}
    return dna
