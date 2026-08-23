"""L3 soft perceptual/aesthetic metrics with optional LPIPS/DreamSim adapters."""

from __future__ import annotations

from typing import Any, Mapping


def run_perceptual_qa(metrics: Mapping[str, Any]) -> dict[str, Any]:
    values = dict(metrics.get("metrics", metrics))
    score = float(values.get("overall_style_similarity", values.get("overall_style", 0.0)))
    return {"layer": "L3_perceptual_aesthetic", "passed": True, "soft": True, "score": round(score, 6), "lpips": values.get("lpips"), "dreamsim": values.get("dreamsim"), "calibration": "human_threshold_required"}
