"""Pairwise preference aggregation without neural training dependencies."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence


def score_preference_pair(pair: Mapping[str, Any], scores: Mapping[str, float]) -> dict[str, Any]:
    left, right = str(pair.get("left_id", "")), str(pair.get("right_id", ""))
    winner = str(pair.get("preferred") or pair.get("winner", ""))
    loser = str(pair.get("rejected") or (right if winner == left else left))
    reasons = list(pair.get("reason_codes") or pair.get("reasons", []))
    return {"left_id": left, "right_id": right, "winner": winner, "preferred": winner, "rejected": loser, "margin": round(float(scores.get(winner, 0.0)) - float(scores.get(loser, 0.0)), 6), "reasons": reasons, "reason_codes": reasons, "figure_family": pair.get("figure_family", ""), "task_id": pair.get("task_id", "")}


def aggregate_elo(pairs: Sequence[Mapping[str, Any]], *, initial: float = 1000.0, k: float = 24.0) -> dict[str, float]:
    ratings: dict[str, float] = defaultdict(lambda: initial)
    for pair in pairs:
        left, right = str(pair.get("left_id")), str(pair.get("right_id"))
        winner = str(pair.get("preferred") or pair.get("winner"))
        if winner not in {left, right}:
            continue
        expected = 1.0 / (1.0 + 10 ** ((ratings[right] - ratings[left]) / 400.0))
        actual = 1.0 if winner == left else 0.0
        ratings[left] += k * (actual - expected)
        ratings[right] += k * ((1.0 - actual) - (1.0 - expected))
    return {key: round(value, 3) for key, value in sorted(ratings.items())}
