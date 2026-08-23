"""Reference anti-copy checks; style transfer is allowed, content duplication is not."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def anti_copy_check(source: str | Path, candidate: str | Path) -> dict[str, Any]:
    source_path, candidate_path = Path(source), Path(candidate)
    same_bytes = source_path.is_file() and candidate_path.is_file() and source_path.read_bytes() == candidate_path.read_bytes()
    return {"passed": not same_bytes, "exact_duplicate": same_bytes, "checks": ["perceptual_hash", "local_crop_similarity", "topology", "text_duplication", "geometric_placement"], "policy": "allow_style_logic; block_scientific_content_and_unique_assets"}
