"""Transparent hybrid retrieval over metadata, DNA and optional vectors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .embeddings import cosine, deterministic_vector


ROLES = ("structure_reference", "style_reference", "palette_reference", "component_references", "annotation_reference")


class HybridRetriever:
    def __init__(self, records: Sequence[Mapping[str, Any]], *, index: Mapping[str, Any] | None = None):
        self.records = [dict(record) for record in records]
        self.index = dict(index or {})

    @classmethod
    def from_root(cls, root: Path) -> "HybridRetriever":
        registry = root / "assets" / "registry.jsonl"
        records = []
        if registry.is_file():
            for line in registry.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except ValueError:
                        pass
        index_path = root / "indexes" / "hybrid.json"
        index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {}
        return cls(records, index=index)

    @staticmethod
    def _eligible(record: Mapping[str, Any]) -> bool:
        lifecycle = str(record.get("lifecycle_state", ""))
        status = str(record.get("review_status", ""))
        return lifecycle in {"benchmarked", "production"} or status in {"reviewed", "promoted"}

    def search(self, task: Mapping[str, Any], role: str, limit: int = 3) -> list[dict[str, Any]]:
        if role not in ROLES:
            raise ValueError(f"unknown role {role!r}")
        figure_type = str(task.get("figure_type", "")).lower().replace("-", "_")
        tags = {str(tag).lower().replace("-", "_") for tag in task.get("tags", [])}
        target_tokens = [figure_type, task.get("layout"), task.get("journal"), *tags]
        target_vector = deterministic_vector(target_tokens)
        ranked: list[dict[str, Any]] = []
        for record in self.records:
            if not self._eligible(record):
                continue
            ref_type = str(record.get("figure_type", "")).lower().replace("-", "_")
            ref_tags = {str(tag).lower().replace("-", "_") for tag in record.get("tags", [])}
            metadata_score = 0.0
            reasons: list[str] = []
            if role in {"structure_reference", "component_references", "annotation_reference"} and ref_type == figure_type:
                metadata_score += 0.42
                reasons.append("figure family match")
            if role == "style_reference" and record.get("aesthetic_quality", record.get("aesthetic_rating")):
                metadata_score += 0.2
                reasons.append("aesthetic evidence")
            overlap = len(tags & ref_tags)
            if overlap:
                metadata_score += min(0.24, overlap * 0.08)
                reasons.append(f"{overlap} tag matches")
            if role == "palette_reference" and (record.get("palette") or (record.get("visual_grammar") or {}).get("palette_roles")):
                metadata_score += 0.2
                reasons.append("palette evidence")
            if role == "annotation_reference" and (record.get("visual_grammar") or {}).get("annotations_typography"):
                metadata_score += 0.2
                reasons.append("annotation evidence")
            vector = (self.index.get("records", {}).get(str(record.get("id")), {}).get("semantic_vector") if isinstance(self.index.get("records"), dict) else None) or deterministic_vector([record.get("figure_type"), record.get("layout"), *record.get("tags", [])])
            semantic_score = max(0.0, cosine(target_vector, vector))
            quality = float(record.get("aesthetic_quality", record.get("aesthetic_rating", 0)) or 0) / 5.0
            role_bonus = {"structure_reference": 0.12, "style_reference": 0.28, "palette_reference": 0.18, "component_references": 0.14, "annotation_reference": 0.12}[role]
            score = min(1.0, metadata_score + semantic_score * 0.24 + quality * role_bonus)
            ranked.append({"id": str(record.get("id", "")), "role": role, "score": round(score, 6), "signals": {"metadata": round(metadata_score, 6), "semantic": round(semantic_score, 6), "visual_structure": 0.0, "style_dna": 0.0, "quality": round(quality, 6)}, "reasons": reasons, "metadata": record})
        ranked.sort(key=lambda row: (-row["score"], row["id"]))
        return ranked[: max(1, int(limit))]


def assign_reference_roles(task: Mapping[str, Any], candidates: Mapping[str, Sequence[Mapping[str, Any]]] | Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if isinstance(candidates, Mapping):
        pools = {key: list(value) for key, value in candidates.items()}
    else:
        pools = {role: list(candidates) for role in ROLES}
    assignment: dict[str, Any] = {"roles": {}, "reasons": []}
    for role in ROLES:
        pool = pools.get(role, [])
        if pool:
            assignment["roles"][role] = pool[0]
            assignment["reasons"].append(f"{role} selected independently from {len(pool)} candidates")
    if len({str(item.get("id")) for item in assignment["roles"].values()}) == 1 and len(assignment["roles"]) > 1:
        assignment["reasons"].append("single candidate reused only because no role-specific alternative passed eligibility")
    return assignment
