#!/usr/bin/env python3
"""Small deterministic helpers for rendered visual-evidence gates."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops, ImageStat


def load_image(path: Path | str) -> Image.Image:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Image is missing: {path}")
    try:
        with Image.open(path) as image:
            image.load()
            if image.width < 2 or image.height < 2:
                raise ValueError(f"Image is too small: {path}")
            return image.convert("RGB")
    except (OSError, SyntaxError) as exc:
        raise ValueError(f"Not a readable image: {path}") from exc


def compose_equal_size_comparison(
    image_paths: Iterable[Path | str], output_path: Path | str
) -> Path:
    """Place images in equal cells without changing their aspect ratios."""
    images = [load_image(path) for path in image_paths]
    canvas = _compose_equal_size(images)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    return output


def _compose_equal_size(images: list[Image.Image]) -> Image.Image:
    if len(images) < 2:
        raise ValueError("A comparison requires at least two images.")
    cell_width = max(image.width for image in images)
    cell_height = max(image.height for image in images)
    canvas = Image.new("RGB", (cell_width * len(images), cell_height), "white")
    for index, image in enumerate(images):
        scale = min(cell_width / image.width, cell_height / image.height)
        fitted = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
        x = index * cell_width + (cell_width - fitted.width) // 2
        y = (cell_height - fitted.height) // 2
        canvas.paste(fitted, (x, y))
    return canvas


def comparison_contains(
    comparison_path: Path | str,
    image_paths: Iterable[Path | str],
    rms_tolerance: float = 3.0,
) -> bool:
    """Verify a standard equal-cell comparison contains the supplied images."""
    sources = [load_image(path) for path in image_paths]
    comparison = load_image(comparison_path)
    if comparison.width % len(sources) != 0:
        return False
    cell_width = comparison.width // len(sources)
    if cell_width < 2:
        return False
    expected = _compose_equal_size(sources)
    if expected.size != comparison.size:
        return False
    diff = ImageChops.difference(expected, comparison)
    values = ImageStat.Stat(diff).rms
    rms = math.sqrt(sum(value * value for value in values) / len(values))
    return rms <= rms_tolerance
