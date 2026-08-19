"""Executable, dependency-light visual comparison for reference alignment.

This is a gate signal, not a claim of perceptual equivalence.  It measures the
observable raster properties that are most useful for catching a stale style
or a retained old skeleton before human review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
from PIL import Image


def _load(path: str | Path, size: Tuple[int, int] = (256, 256)) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return np.asarray(canvas, dtype=np.float32) / 255.0


def _ink(img: np.ndarray) -> np.ndarray:
    # Treat near-white anti-aliased pixels as whitespace. This is intentionally
    # tolerant of white, ivory, and transparent-background exports.
    return np.min(img, axis=2) < 0.88


def _runs(values: np.ndarray, threshold: float = 0.02) -> list[tuple[int, int]]:
    active = values > threshold
    runs: list[tuple[int, int]] = []
    start = None
    for idx, yes in enumerate(active):
        if yes and start is None:
            start = idx
        elif not yes and start is not None:
            if idx - start >= 2:
                runs.append((start, idx))
            start = None
    if start is not None and len(active) - start >= 2:
        runs.append((start, len(active)))
    return runs


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    den = float(np.linalg.norm(a) * np.linalg.norm(b))
    if den == 0:
        return 1.0 if np.allclose(a, b) else 0.0
    return float(np.clip(np.dot(a, b) / den, 0, 1))


def _palette(img: np.ndarray, count: int = 8) -> np.ndarray:
    pixels = img.reshape(-1, 3)
    pixels = pixels[np.min(pixels, axis=1) < 0.9]
    if len(pixels) == 0:
        return np.zeros((0, 3), dtype=np.float32)
    # Histogram quantisation is deterministic and avoids a heavyweight ML
    # dependency. Dominant colors are role-level evidence, not exact samples.
    bins = np.clip((pixels * 8).astype(int), 0, 7)
    keys, counts = np.unique(bins[:, 0] * 64 + bins[:, 1] * 8 + bins[:, 2], return_counts=True)
    order = np.argsort(counts)[::-1][:count]
    out = []
    for idx in order:
        key = int(keys[idx])
        out.append([(key // 64 + 0.5) / 8, ((key % 64) // 8 + 0.5) / 8, (key % 8 + 0.5) / 8])
    return np.asarray(out, dtype=np.float32)


def _palette_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) == 0 or len(b) == 0:
        return 1.0 if len(a) == len(b) else 0.0
    distances = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2))
    return float(np.mean(np.exp(-4.0 * np.min(distances, axis=1))))


def _component_signature(mask: np.ndarray) -> np.ndarray:
    # Coarse occupancy retains panel topology and whitespace rhythm while being
    # robust to different text content and dimensions.
    by_row = mask.mean(axis=1)
    by_col = mask.mean(axis=0)
    return np.concatenate([by_row.reshape(32, -1).mean(axis=1), by_col.reshape(-1, 32).mean(axis=0)])


def compare_output_to_reference(reference: str | Path, output: str | Path) -> Dict[str, Any]:
    ref = _load(reference)
    cand = _load(output)
    rm, cm = _ink(ref), _ink(cand)
    rsig, csig = _component_signature(rm), _component_signature(cm)
    ref_ratio, cand_ratio = float(rm.mean()), float(cm.mean())
    ref_rows, cand_rows = rm.mean(axis=1), cm.mean(axis=1)
    ref_cols, cand_cols = rm.mean(axis=0), cm.mean(axis=0)
    # Edge density is a useful proxy for stroke/marker rhythm at this stage.
    redge = np.abs(np.diff(rm.astype(float), axis=0)).mean() + np.abs(np.diff(rm.astype(float), axis=1)).mean()
    cedge = np.abs(np.diff(cm.astype(float), axis=0)).mean() + np.abs(np.diff(cm.astype(float), axis=1)).mean()
    corner_ref = np.array([rm[:64, :64].mean(), rm[:64, -64:].mean(), rm[-64:, :64].mean(), rm[-64:, -64:].mean()])
    corner_cand = np.array([cm[:64, :64].mean(), cm[:64, -64:].mean(), cm[-64:, :64].mean(), cm[-64:, -64:].mean()])
    metrics = {
        "layout_topology_similarity": _cosine(rsig, csig),
        "panel_proportion_similarity": 1.0 - min(1.0, abs(float(_runs(ref_cols, .03).__len__() - _runs(cand_cols, .03).__len__())) / 4.0),
        "whitespace_similarity": 1.0 - min(1.0, abs(ref_ratio - cand_ratio) / 0.35),
        "typography_hierarchy_similarity": _cosine(np.array([rm[...,:].mean(), rm[:64].mean(), rm[-64:].mean()]), np.array([cm[...,:].mean(), cm[:64].mean(), cm[-64:].mean()])),
        "palette_role_similarity": _palette_similarity(_palette(ref), _palette(cand)),
        "stroke_marker_similarity": 1.0 - min(1.0, abs(float(redge - cedge)) / 0.25),
        "legend_annotation_similarity": 1.0 - min(1.0, float(np.mean(np.abs(corner_ref - corner_cand))) / 0.25),
        "density_similarity": 1.0 - min(1.0, abs(ref_ratio - cand_ratio) / 0.35),
    }
    weights = {"layout_topology_similarity": .2, "panel_proportion_similarity": .12, "whitespace_similarity": .1, "typography_hierarchy_similarity": .1, "palette_role_similarity": .15, "stroke_marker_similarity": .1, "legend_annotation_similarity": .08, "density_similarity": .15}
    overall = sum(metrics[k] * w for k, w in weights.items()) / sum(weights.values())
    metrics["overall_style_similarity"] = float(np.clip(overall, 0, 1))
    return {"reference": str(reference), "output": str(output), "metrics": {k: round(float(v), 4) for k, v in metrics.items()}, "verdict": "pass" if metrics["overall_style_similarity"] >= 0.72 else "fix"}
