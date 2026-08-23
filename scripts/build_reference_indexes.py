#!/usr/bin/env python3
"""Build transparent hybrid reference indexes for the reference collection."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
from publication_figure_design.reference_intelligence.embeddings import record_vectors  # noqa: E402


def build_indexes(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    reference_root = root / "assets" / "visual-references"
    records = []
    for metadata_path in sorted(reference_root.glob("**/metadata.json")):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if metadata.get("scope") not in {None, "references", "generated-archive"}:
            continue
        records.append(metadata)

    inverted: dict[str, list[str]] = {}
    layout: dict[str, dict[str, Any]] = {}
    style: dict[str, dict[str, Any]] = {}
    component: dict[str, dict[str, Any]] = {}
    semantic: dict[str, dict[str, Any]] = {}
    hybrid_records: dict[str, dict[str, Any]] = {}
    for record in records:
        ref_id = str(record.get("id", ""))
        for token in [record.get("figure_type"), record.get("subtype"), *(record.get("tags") or [])]:
            if token:
                inverted.setdefault(str(token).strip().lower(), []).append(ref_id)
        grammar = record.get("visual_grammar") or {}
        layout[ref_id] = {
            "figure_type": record.get("figure_type"),
            "layout": record.get("layout"),
            "canvas_composition": grammar.get("canvas_composition"),
            "panel_topology": grammar.get("repetition_structures", {}).get("topology") if isinstance(grammar.get("repetition_structures"), dict) else None,
        }
        style[ref_id] = {
            "aesthetic_quality": record.get("aesthetic_quality", record.get("aesthetic_rating")),
            "palette_roles": grammar.get("palette_roles"),
            "annotations_typography": grammar.get("annotations_typography"),
            "style_spec_path": record.get("style_spec_path"),
        }
        component[ref_id] = {
            "figure_type": record.get("figure_type"),
            "objects_material": grammar.get("objects_material"),
            "connectors": grammar.get("connectors"),
            "legend_key": grammar.get("legend_key"),
            "chart_marks_axes": grammar.get("chart_marks_axes"),
        }
        card: dict[str, Any] = {}
        card_path = record.get("figure_card_path")
        if card_path:
            candidate = root / str(card_path)
            if candidate.is_file():
                try:
                    card = json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    card = {}
        canvas = card.get("canvas") if isinstance(card, dict) else {}
        geometry = card.get("geometry") if isinstance(card, dict) else {}
        canvas = canvas if isinstance(canvas, dict) else {}
        geometry = geometry if isinstance(geometry, dict) else {}
        semantic[ref_id] = {
            "model_version": "hybrid-deterministic",
            "vector": [
                float(canvas.get("aspect_ratio", 0.0) or 0.0),
                float(card.get("ink_coverage", 0.0) or 0.0),
                float(geometry.get("whitespace_fraction", 0.0) or 0.0),
                float(record.get("aesthetic_quality", record.get("aesthetic_rating", 0.0)) or 0.0),
            ],
        }
        dna = {}
        dna_path = record.get("reference_dna_path")
        if dna_path and (root / str(dna_path)).is_file():
            try:
                dna = json.loads((root / str(dna_path)).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                dna = {}
        hybrid_records[ref_id] = {
            "semantic_vector": record_vectors(record, dna).get("semantic", []),
            "structure_vector": record_vectors(record, dna).get("structure", []),
            "style_vector": record_vectors(record, dna).get("style", []),
            "dna_path": dna_path,
        }

    out_dir = root / "indexes"
    out_dir.mkdir(parents=True, exist_ok=True)
    registry_path = root / "assets" / "registry.jsonl"
    corpus_bytes = registry_path.read_bytes() if registry_path.is_file() else b""
    corpus_sha256 = hashlib.sha256(corpus_bytes).hexdigest()
    index_version = f"hybrid-deterministic-{corpus_sha256[:12]}"
    semantic_version = f"semantic-deterministic-{corpus_sha256[:12]}"
    provenance = {
        "index_version": index_version,
        "semantic_model_version": semantic_version,
        "schema_version": "1.0",
        "embedding_model": "deterministic-semantic-structure-style",
        "optional_backends": {"semantic": "siglip2", "visual_structure": "dinov2_or_dinov3"},
        "built_at": datetime.now(timezone.utc).isoformat(),
        "corpus_sha256": corpus_sha256,
        "record_count": len(records),
    }
    common = {
        "schema_version": "1.0",
        "model_version": index_version,
        "aliases": {"current": index_version},
        "provenance": provenance,
        "record_count": len(records),
    }
    for value in semantic.values():
        value["model_version"] = semantic_version
    outputs = {
        "metadata_inverted.json": {**common, "index_type": "metadata_inverted", "terms": {k: sorted(v) for k, v in sorted(inverted.items())}},
        "layout.json": {**common, "index_type": "layout", "records": layout},
        "style.json": {**common, "index_type": "style", "records": style},
        "component.json": {**common, "index_type": "component", "records": component},
        "semantic.json": {**common, "index_type": "semantic", "records": semantic},
        "hybrid.json": {**common, "index_type": "hybrid", "records": hybrid_records},
    }
    for name, payload in outputs.items():
        (out_dir / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return {"records": len(records), "files": [str(out_dir / name) for name in outputs]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(build_indexes(args.root), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
