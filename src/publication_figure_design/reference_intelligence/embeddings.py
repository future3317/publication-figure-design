"""Optional embedding adapters and deterministic feature vectors."""

from __future__ import annotations

import hashlib
import math
from typing import Any, Iterable, Mapping

import numpy as np


def _hash_token(token: str, size: int) -> int:
    return int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16) % size


def deterministic_vector(values: Iterable[Any], size: int = 32) -> list[float]:
    vector = np.zeros(size, dtype=np.float32)
    for value in values:
        token = str(value).strip().lower()
        if not token:
            continue
        idx = _hash_token(token, size)
        vector[idx] += 1.0
    norm = float(np.linalg.norm(vector))
    return (vector / norm if norm else vector).round(6).tolist()


def record_vectors(metadata: Mapping[str, Any], dna: Mapping[str, Any] | None = None) -> dict[str, list[float]]:
    dna = dict(dna or {})
    composition = dict(dna.get("composition") or {})
    palette = dict(dna.get("palette") or {})
    style = dict(dna.get("style") or {})
    semantic_tokens = [metadata.get("figure_type"), metadata.get("subtype"), *(metadata.get("tags") or []), style.get("style_cluster")]
    structure_tokens = [metadata.get("figure_type"), metadata.get("layout"), composition.get("panel_count"), composition.get("aspect_ratio"), composition.get("reading_order")]
    style_tokens = [*(metadata.get("tags") or []), *(palette.get("semantic_roles") or []), style.get("quality_score")]
    return {"semantic": deterministic_vector(semantic_tokens), "structure": deterministic_vector(structure_tokens), "style": deterministic_vector(style_tokens)}


def cosine(a: Iterable[float], b: Iterable[float]) -> float:
    av = np.asarray(list(a), dtype=np.float32)
    bv = np.asarray(list(b), dtype=np.float32)
    if av.size == 0 or bv.size == 0:
        return 0.0
    den = float(np.linalg.norm(av) * np.linalg.norm(bv))
    return float(np.clip(np.dot(av, bv) / den, -1.0, 1.0)) if den else 0.0


def optional_model_backend(name: str) -> str:
    """Return an available optional backend without importing/downloads by default."""
    if name == "siglip2":
        try:
            import transformers  # type: ignore  # noqa: F401
            return "siglip2-optional"
        except ImportError:
            return "deterministic-text-fallback"
    if name in {"dinov2", "dinov3"}:
        try:
            import torch  # type: ignore  # noqa: F401
            return f"{name}-optional"
        except ImportError:
            return "deterministic-visual-fallback"
    return "deterministic-fallback"
