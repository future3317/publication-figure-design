#!/usr/bin/env python3
"""Build deterministic metadata/layout/style/component indexes for references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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
            "model_version": "deterministic-proxy-current",
            "vector": [
                float(canvas.get("aspect_ratio", 0.0) or 0.0),
                float(card.get("ink_coverage", 0.0) or 0.0),
                float(geometry.get("whitespace_fraction", 0.0) or 0.0),
                float(record.get("aesthetic_quality", record.get("aesthetic_rating", 0.0)) or 0.0),
            ],
        }

    out_dir = root / "indexes"
    out_dir.mkdir(parents=True, exist_ok=True)
    common = {"schema_version": "1.0", "model_version": "metadata-current", "record_count": len(records)}
    outputs = {
        "metadata_inverted.json": {**common, "index_type": "metadata_inverted", "terms": {k: sorted(v) for k, v in sorted(inverted.items())}},
        "layout.json": {**common, "index_type": "layout", "records": layout},
        "style.json": {**common, "index_type": "style", "records": style},
        "component.json": {**common, "index_type": "component", "records": component},
        "semantic.json": {**common, "index_type": "semantic_proxy", "records": semantic},
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
