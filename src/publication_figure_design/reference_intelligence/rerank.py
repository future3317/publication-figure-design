"""Small task-compatibility reranker used after hybrid retrieval."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def rerank(candidates: Sequence[Mapping[str, Any]], task: Mapping[str, Any], *, role: str) -> list[dict[str, Any]]:
    target = str(task.get("figure_type", "")).lower().replace("-", "_")
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        row = dict(candidate)
        metadata = dict(row.get("metadata") or {})
        score = float(row.get("score", 0.0))
        if role != "style_reference" and str(metadata.get("figure_type", "")).lower().replace("-", "_") == target:
            score += 0.08
        if metadata.get("production_ready") is True:
            score += 0.05
        row["score"] = round(min(1.0, score), 6)
        rows.append(row)
    return sorted(rows, key=lambda item: (-item["score"], str(item.get("id", ""))))
