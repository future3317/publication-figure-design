#!/usr/bin/env python3
"""Build a compact, code-free retrieval catalog from a ChartMimic JSONL file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _family(name: str) -> str:
    stem = name.lower()
    for token, family in (
        ("heat", "heatmap"), ("bar", "bar"), ("line", "line"),
        ("scatter", "scatter"), ("box", "distribution"), ("violin", "distribution"),
        ("hist", "distribution"), ("3d", "three_dimensional"),
        ("radar", "radial"), ("pie", "part_to_whole"),
    ):
        if token in stem:
            return family
    return "other"


def build_catalog(source: Path | str, output: Path | str | None = None) -> dict[str, Any]:
    source_path = Path(source)
    items: list[dict[str, Any]] = []
    with source_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            idx = str(record.get("idx") or Path(str(record.get("file", line_number))).stem)
            width = float(record["width"]) if record.get("width") is not None else None
            height = float(record["height"]) if record.get("height") is not None else None
            items.append({
                "id": idx,
                "file": str(record.get("file", "")),
                "family": _family(str(record.get("file", idx))),
                "width_in": width,
                "height_in": height,
                "aspect_ratio": round(width / height, 6) if width and height else None,
                "code_path": f"{source_path.name}#{idx}",
                "line": line_number,
            })
    catalog = {
        "schema": "publication-figure-design/chartmimic-catalog",
        "source": {"name": "ChartMimic", "file": source_path.name, "kind": "external-benchmark"},
        "count": len(items),
        "items": items,
    }
    if output is not None:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalog = build_catalog(args.source, args.output)
    print(f"ChartMimic catalog: {catalog['count']} items -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
