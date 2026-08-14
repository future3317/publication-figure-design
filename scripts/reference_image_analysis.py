#!/usr/bin/env python3
"""Extract objective image evidence for a reference ``figure_card.json``.

The card deliberately separates measurable pixels (canvas, background, ink,
palette) from fields that require human/agent interpretation (panels, axes,
typography, and annotation semantics).  It is an intake aid, not a chart
classifier and never replaces opening the reference at final size.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _near_white(rgb: tuple[float, float, float]) -> bool:
    return min(rgb) >= 242 and max(rgb) - min(rgb) <= 10


def _dominant(image: Image.Image, limit: int = 8) -> list[dict[str, Any]]:
    """Return dominant colors, preferring the optional extraction packages."""
    try:
        import extcolors  # type: ignore

        colors, total = extcolors.extract_from_image(image, tolerance=12, limit=limit)
        values = [(tuple(int(v) for v in rgb), int(count)) for rgb, count in colors]
    except Exception:
        # Pillow's quantizer is deterministic and keeps the analyzer usable in
        # the minimal skill runtime when optional palette packages are absent.
        quantized = image.convert("RGB").quantize(colors=max(limit, 2), method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette() or []
        counts = quantized.getcolors(maxcolors=image.width * image.height) or []
        values = []
        for count, index in sorted(counts, reverse=True)[:limit]:
            start = int(index) * 3
            values.append((tuple(int(v) for v in palette[start : start + 3]), int(count)))

    total = max(1, sum(count for _, count in values))
    result: list[dict[str, Any]] = []
    for rgb, count in values:
        role = "background" if _near_white(tuple(float(v) for v in rgb)) else "data_or_annotation"
        result.append({"hex": _hex(rgb), "rgb": list(rgb), "fraction": round(count / total, 6), "role": role})
    return result


def analyze_image(
    image_path: Path | str,
    *,
    output: Path | str | None = None,
    figure_type: str = "unknown",
    source: str = "user-supplied",
) -> dict[str, Any]:
    """Analyze one image and optionally write a JSON figure card."""
    path = Path(image_path)
    with Image.open(path) as opened:
        image = opened.convert("RGB")
    pixels = np.asarray(image, dtype=np.float32)
    h, w = pixels.shape[:2]
    corners = np.array([pixels[0, 0], pixels[0, -1], pixels[-1, 0], pixels[-1, -1]])
    background_rgb = tuple(float(v) for v in corners.mean(axis=0))
    distance = np.linalg.norm(pixels - np.asarray(background_rgb, dtype=np.float32), axis=2)
    ink_coverage = float(np.mean(distance > 18.0))
    card: dict[str, Any] = {
        "schema": "publication-figure-design/figure-card-v1",
        "source": source,
        "figure_type": figure_type,
        "canvas": {
            "width_px": int(w),
            "height_px": int(h),
            "aspect_ratio": round(w / max(h, 1), 6),
            "mode": "RGB",
        },
        "background": {
            "rgb": [round(v, 3) for v in background_rgb],
            "hex": _hex(tuple(int(round(v)) for v in background_rgb)),
            "near_white": _near_white(background_rgb),
        },
        "ink_coverage": round(ink_coverage, 6),
        "palette": {"dominant": _dominant(image), "extraction": "extcolors-or-pillow-quantize"},
        "panels": {"status": "manual_required", "count": None, "layout": None},
        "axes": {"status": "manual_required"},
        "typography": {"status": "manual_required"},
        "annotations": {"status": "manual_required"},
    }
    if output is not None:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return card


def compare_images(reference_path: Path | str, candidate_path: Path | str) -> dict[str, Any]:
    """Return a small, reproducible pixel comparison for equal-size images."""
    with Image.open(reference_path) as ref_open, Image.open(candidate_path) as cand_open:
        reference = np.asarray(ref_open.convert("L"), dtype=np.float32)
        candidate = np.asarray(cand_open.convert("L"), dtype=np.float32)
    report: dict[str, Any] = {
        "reference_size": [int(reference.shape[1]), int(reference.shape[0])],
        "candidate_size": [int(candidate.shape[1]), int(candidate.shape[0])],
        "size_match": bool(reference.shape == candidate.shape),
    }
    if not report["size_match"]:
        report["size"] = None
        report["ssim"] = None
        return report
    report["size"] = [int(reference.shape[1]), int(reference.shape[0])]
    try:
        from skimage.metrics import structural_similarity

        score = float(structural_similarity(reference, candidate, data_range=255.0))
    except Exception:
        mse = float(np.mean((reference - candidate) ** 2))
        score = float(max(0.0, 1.0 - mse / (255.0**2)))
    report["ssim"] = round(score, 6)
    report["mean_absolute_error"] = round(float(np.mean(np.abs(reference - candidate))), 6)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("image", type=Path)
    analyze.add_argument("--output", type=Path, required=True)
    analyze.add_argument("--figure-type", default="unknown")
    compare = sub.add_parser("compare")
    compare.add_argument("reference", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "analyze":
        print(json.dumps(analyze_image(args.image, output=args.output, figure_type=args.figure_type), indent=2, ensure_ascii=False))
    else:
        report = compare_images(args.reference, args.candidate)
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            args.output.write_text(text + "\n", encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
