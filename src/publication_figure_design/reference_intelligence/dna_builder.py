"""Build and persist ReferenceDNA for an ingested reference directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .analyzers import analyze_code, analyze_pdf, analyze_raster, analyze_svg
from .dna import ReferenceDNA


def _source_path(reference_dir: Path, metadata: Mapping[str, Any]) -> Path:
    for key in ("source_path", "image_path", "code_path"):
        value = metadata.get(key)
        if value:
            path = Path(str(value))
            candidate = path if path.is_absolute() else reference_dir.parents[4] / path
            if candidate.is_file():
                return candidate
    for suffixes in ((".svg",), (".pdf",), (".py",), (".png", ".jpg", ".jpeg")):
        for suffix in suffixes:
            matches = sorted(reference_dir.glob(f"*{suffix}"))
            if matches:
                return matches[0]
    raise FileNotFoundError(f"no supported source in {reference_dir}")


def build_reference_dna(reference_dir: Path, *, metadata: Mapping[str, Any] | None = None) -> ReferenceDNA:
    reference_dir = Path(reference_dir)
    meta_path = reference_dir / "metadata.json"
    meta = dict(metadata or {})
    if meta_path.is_file():
        meta.update(json.loads(meta_path.read_text(encoding="utf-8")))
    source = _source_path(reference_dir, meta)
    suffix = source.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        dna = analyze_raster(source, metadata=meta)
    elif suffix == ".svg":
        dna = analyze_svg(source, metadata=meta)
    elif suffix == ".pdf":
        dna = analyze_pdf(source, metadata=meta)
    elif suffix == ".py":
        dna = analyze_code(source, metadata=meta)
    else:
        raise ValueError(f"unsupported reference source type: {source.suffix}")
    output = reference_dir / "reference_dna.json"
    output.write_text(json.dumps(dna.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dna


def load_reference_dna(reference_dir: Path) -> ReferenceDNA:
    payload = json.loads((Path(reference_dir) / "reference_dna.json").read_text(encoding="utf-8"))
    return ReferenceDNA(**{key: payload.get(key, {}) for key in ("identity", "composition", "palette", "typography", "geometry", "annotations", "hierarchy", "style", "constraints", "embeddings", "confidence", "extensions")}, schema=payload.get("schema", "publication-figure-design/reference-dna"), schema_version=str(payload.get("schema_version", "2.0")))
