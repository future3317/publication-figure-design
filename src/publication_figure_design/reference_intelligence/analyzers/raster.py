"""Conservative raster analyzer that reuses the existing figure-card fields."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ..dna import ReferenceDNA


def analyze_raster(path: Path, *, metadata: Mapping[str, Any] | None = None) -> ReferenceDNA:
    from PIL import Image
    import numpy as np
    with Image.open(path) as opened:
        image = opened.convert("RGB")
        original_size = image.size
        if max(image.size) > 1200:
            scale = 1200 / max(image.size)
            image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.LANCZOS)
        pixels = np.asarray(image, dtype=np.float32)
    background = pixels[[0, -1], :][:, [0, -1]].reshape(-1, 3).mean(axis=0)
    ink = np.linalg.norm(pixels - background, axis=2) > 18
    card = {"canvas": {"width_px": original_size[0], "height_px": original_size[1], "aspect_ratio": original_size[0] / max(original_size[1], 1)}, "background": {"rgb": background.tolist(), "hex": "#ffffff"}, "ink_coverage": float(ink.mean()), "geometry": {"whitespace_fraction": float(1 - ink.mean())}, "palette": {"dominant": []}, "panels": {"count": 1, "bboxes_px": []}, "whitespace_map": {"fraction": float(1 - ink.mean())}, "visual_density": float(ink.mean())}
    meta = dict(metadata or {})
    meta.setdefault("reference_kind", "raster")
    meta.setdefault("confidence", {})
    dna = ReferenceDNA.from_metadata(meta, card=card)
    dna.typography.update({"font_family_class": "sans_serif_unknown", "exactness": "relative_only"})
    dna.confidence.setdefault("composition", 0.72)
    dna.confidence.setdefault("palette", 0.68)
    dna.confidence.setdefault("typography", 0.35)
    return dna
