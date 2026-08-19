#!/usr/bin/env python3
"""Extract objective image evidence for a reference ``figure_card.json``.

The card deliberately separates measurable pixels (canvas, background, ink,
palette) from fields that require human/agent interpretation (panels, axes,
typography, and annotation semantics).  It is an intake aid, not a chart
classifier and never replaces opening the reference at final size.
"""

from __future__ import annotations

import argparse
import hashlib
import io
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
        try:
            from colorthief import ColorThief  # type: ignore

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            colors = ColorThief(buffer).get_palette(color_count=limit, quality=1)
            pixels = np.asarray(image, dtype=np.float32).reshape(-1, 3)
            values = []
            for color in colors:
                rgb = np.asarray(color, dtype=np.float32)
                count = int(np.sum(np.linalg.norm(pixels - rgb, axis=1) < 24.0))
                values.append((tuple(int(v) for v in color), max(count, 1)))
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


def _perceptual_hash(image: Image.Image) -> str:
    """Compact DCT hash used to identify visually near-identical references."""
    gray = image.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
    pixels = np.asarray(gray, dtype=np.float32)
    n = pixels.shape[0]
    basis = np.cos(np.pi * (2 * np.arange(n)[:, None] + 1) * np.arange(8)[None, :] / (2 * n))
    low = (basis.T @ pixels @ basis)[:8, :8]
    threshold = float(np.median(low[1:, 1:]))
    bits = (low >= threshold).astype(np.uint8).flatten()
    return "".join(f"{int(bits[i:i + 4].dot([8, 4, 2, 1])):x}" for i in range(0, 64, 4))


def _content_geometry(pixels: np.ndarray, background_rgb: tuple[float, float, float]) -> dict[str, Any]:
    distance = np.linalg.norm(pixels - np.asarray(background_rgb, dtype=np.float32), axis=2)
    ink = distance > 18.0
    ys, xs = np.where(ink)
    h, w = ink.shape
    if len(xs):
        bbox = [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]
    else:
        bbox = [0, 0, int(w), int(h)]
    row_ink = ink.mean(axis=1)
    col_ink = ink.mean(axis=0)
    return {
        "content_bbox_px": bbox,
        "whitespace_fraction": round(float(1.0 - ink.mean()), 6),
        "row_density_peaks": [int(i) for i in np.argsort(row_ink)[-min(5, h):][::-1]],
        "column_density_peaks": [int(i) for i in np.argsort(col_ink)[-min(5, w):][::-1]],
        "ink_density": round(float(ink.mean()), 6),
    }


def _visual_proxies(pixels: np.ndarray, geometry: dict[str, Any]) -> dict[str, Any]:
    """Extract conservative, measurable proxies for reviewable visual structure."""
    gray = pixels.mean(axis=2)
    dark = gray < 100
    h, w = dark.shape
    border = max(2, min(h, w) // 100)
    edge_density = {
        "top": round(float(dark[:border].mean()), 6),
        "bottom": round(float(dark[-border:].mean()), 6),
        "left": round(float(dark[:, :border].mean()), 6),
        "right": round(float(dark[:, -border:].mean()), 6),
    }
    row_density = dark.mean(axis=1)
    col_density = dark.mean(axis=0)
    # Estimate line weight from short contiguous dark runs.  The previous
    # density×canvas heuristic inflated stroke widths on dense charts because
    # it measured how much of a row was inked, not the width of an actual mark.
    runs: list[int] = []
    for line in list(dark) + list(dark.T):
        padded = np.r_[False, line, False]
        starts = np.flatnonzero(padded[1:] & ~padded[:-1])
        ends = np.flatnonzero(~padded[1:] & padded[:-1])
        runs.extend(int(end - start) for start, end in zip(starts, ends) if 1 <= end - start <= 20)
    stroke_median = float(np.median(runs)) if runs else 1.0
    return {
        "axes": {
            "status": "heuristic_pixel_measurement",
            "spines": edge_density,
            "tick_proxy": {"row_peaks": [int(i) for i in np.argsort(row_density)[-8:]], "column_peaks": [int(i) for i in np.argsort(col_density)[-8:]]},
            "grid_proxy": {"horizontal_density": round(float(np.percentile(row_density, 90)), 6), "vertical_density": round(float(np.percentile(col_density, 90)), 6)},
        },
        "typography": {
            "status": "heuristic_ink_hierarchy",
            "font_family": "manual_review_required",
            "hierarchy": [
                {"role": "headline_or_axis", "ink_density_peak": round(float(np.percentile(row_density, 99)), 6)},
                {"role": "body_or_tick", "ink_density_peak": round(float(np.percentile(row_density, 90)), 6)},
            ],
            "size_proxy": {"largest_dark_run_px": int(max(1, np.max(np.diff(np.where(np.r_[True, dark.any(axis=1), True])[0])) - 1))},
        },
        "annotations": {
            "status": "heuristic_density_regions",
            "content_bbox_px": geometry["content_bbox_px"],
            "high_density_rows": [int(i) for i in np.argsort(row_density)[-5:][::-1]],
            "high_density_columns": [int(i) for i in np.argsort(col_density)[-5:][::-1]],
        },
        "marker_family": {"status": "heuristic", "dark_pixel_fraction": round(float(dark.mean()), 6)},
        "stroke_width_px": {"status": "heuristic_short_run_proxy", "median": round(max(1.0, stroke_median), 3)},
        "component_crops": [{"name": "content", "bbox_px": geometry["content_bbox_px"]}],
    }


def analyze_image(
    image_path: Path | str,
    *,
    output: Path | str | None = None,
    figure_type: str = "unknown",
    source: str = "user-supplied",
) -> dict[str, Any]:
    """Analyze one image and optionally write a JSON figure card."""
    path = Path(image_path)
    raw_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as opened:
        original_mode = opened.mode
        has_alpha = "A" in opened.getbands() or "transparency" in opened.info
        colorspace = "embedded_icc" if opened.info.get("icc_profile") else "sRGB_assumed"
        image = opened.convert("RGB")
    pixels = np.asarray(image, dtype=np.float32)
    h, w = pixels.shape[:2]
    corners = np.array([pixels[0, 0], pixels[0, -1], pixels[-1, 0], pixels[-1, -1]])
    background_rgb = tuple(float(v) for v in corners.mean(axis=0))
    distance = np.linalg.norm(pixels - np.asarray(background_rgb, dtype=np.float32), axis=2)
    ink_coverage = float(np.mean(distance > 18.0))
    geometry = _content_geometry(pixels, background_rgb)
    card: dict[str, Any] = {
        "schema": "publication-figure-design/figure-card",
        "schema_version": "2.0",
        "source": source,
        "figure_type": figure_type,
        "source_sha256": raw_sha256,
        "perceptual_hash": _perceptual_hash(image),
        "canvas": {
            "width_px": int(w),
            "height_px": int(h),
            "aspect_ratio": round(w / max(h, 1), 6),
            "mode": original_mode,
            "colorspace": colorspace,
            "has_alpha": bool(has_alpha),
        },
        "background": {
            "rgb": [round(v, 3) for v in background_rgb],
            "hex": _hex(tuple(int(round(v)) for v in background_rgb)),
            "near_white": _near_white(background_rgb),
        },
        "ink_coverage": round(ink_coverage, 6),
        "geometry": geometry,
        "palette": {"dominant": _dominant(image), "extraction": "extcolors-or-pillow-quantize"},
        "panels": {
            "status": "heuristic_single_canvas",
            "count": 1,
            "layout": "single_canvas",
            "bboxes_px": [geometry["content_bbox_px"]],
            "adjacency": [],
            "reading_order": [0],
        },
        "plot_bbox": geometry["content_bbox_px"],
        "whitespace_map": {
            "status": "pixel_density",
            "fraction": geometry["whitespace_fraction"],
        },
        "visual_density": geometry["ink_density"],
        "saliency": {"status": "ink_density_proxy", "bbox_px": geometry["content_bbox_px"]},
        **_visual_proxies(pixels, geometry),
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
