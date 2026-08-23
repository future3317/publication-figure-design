"""PDF analyzer using PyMuPDF when available, without making it core."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ..dna import ReferenceDNA


def analyze_pdf(path: Path, *, metadata: Mapping[str, Any] | None = None) -> ReferenceDNA:
    try:
        import fitz  # type: ignore
    except ImportError:
        dna = ReferenceDNA.from_metadata({**dict(metadata or {}), "reference_kind": "pdf"})
        dna.identity["source_kind"] = "pdf"
        dna.confidence["typography"] = 0.15
        dna.extensions["pdf"] = {"status": "pymupdf_not_installed"}
        return dna
    doc = fitz.open(path)
    spans: list[dict[str, Any]] = []
    drawings = 0
    for page in doc:
        text = page.get_text("dict")
        for block in text.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    spans.append({"font": span.get("font"), "size": span.get("size"), "bbox": span.get("bbox")})
        drawings += len(page.get_drawings())
    families = sorted({str(span.get("font")) for span in spans if span.get("font")})
    sizes = [float(span["size"]) for span in spans if isinstance(span.get("size"), (int, float))]
    dna = ReferenceDNA.from_metadata({**dict(metadata or {}), "reference_kind": "pdf"})
    dna.identity["source_kind"] = "pdf"
    dna.typography.update({"exact_font": families, "family_class": families[0] if families else "sans_serif_unknown", "sizes_pt": sizes, "exactness": "pdf_text_exact"})
    dna.geometry["drawing_count"] = drawings
    dna.confidence.update({"typography": 0.99, "geometry": 0.9})
    dna.extensions["pdf"] = {"page_count": len(doc), "text_spans": spans, "drawing_count": drawings}
    doc.close()
    return dna
