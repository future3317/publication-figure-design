#!/usr/bin/env python3
"""Inspect annotation contrast in a rendered PNG using declared text regions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from PIL import Image

try:
    from .palette_manager import contrast_ratio
except ImportError:  # pragma: no cover - direct CLI execution
    from palette_manager import contrast_ratio


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02X}" for channel in rgb)


def _dominant(colors: Iterable[tuple[int, int, int]]) -> tuple[int, int, int]:
    return Counter(colors).most_common(1)[0][0]


def inspect_text_contrast(
    image_path: Path | str,
    regions: list[tuple[int, int, int, int]],
    minimum_ratio: float = 4.5,
) -> dict:
    """Measure the best glyph-colored cluster against its local tile background."""
    image = Image.open(image_path).convert("RGB")
    results = []
    for region in regions:
        pixels = list(image.crop(region).getdata())
        counts = Counter(pixels)
        background = _dominant(pixels)
        candidates = [color for color in counts if color != background]
        if not candidates:
            results.append({"region": list(region), "contrast_ratio": 0.0, "pass": False,
                            "message": "No annotation pixels found in declared region."})
            continue
        # Antialiasing creates several glyph shades. Select the one with the
        # highest local contrast, which recovers the text stroke color.
        text = max(candidates, key=lambda color: contrast_ratio(_hex(color), _hex(background)))
        ratio = contrast_ratio(_hex(text), _hex(background))
        results.append({
            "region": list(region), "background": _hex(background), "text": _hex(text),
            "contrast_ratio": round(ratio, 3), "pass": ratio >= minimum_ratio,
        })
    return {"ready": bool(results) and all(item["pass"] for item in results), "minimum_ratio": minimum_ratio, "regions": results}


def _parse_region(value: str) -> tuple[int, int, int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("a region must be left,top,right,bottom")
    return tuple(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--regions", type=Path, help="JSON list of [left, top, right, bottom].")
    parser.add_argument("--region", action="append", type=_parse_region, default=[], help="One left,top,right,bottom text box; repeat as needed.")
    parser.add_argument("--minimum-ratio", type=float, default=4.5)
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()
    if args.regions:
        regions = [tuple(region) for region in json.loads(args.regions.read_text(encoding="utf-8"))]
    else:
        regions = args.region
    if not regions:
        parser.error("supply --regions <json> or at least one --region left,top,right,bottom")
    report = inspect_text_contrast(args.image, regions, args.minimum_ratio)
    print(f"Rendered text contrast: {'PASS' if report['ready'] else 'FIX'}")
    for region in report["regions"]:
        print(f"  {region}")
    if args.json_path:
        args.json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
