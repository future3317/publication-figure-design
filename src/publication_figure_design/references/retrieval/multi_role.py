"""Role-separated retrieval for structure, style, components and annotations."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


@dataclass
class RoleMatch:
    id: str
    image_path: Optional[str]
    figure_type: str
    role: str
    reference_alignment_score: float
    aesthetic_quality_score: float
    scientific_correctness_score: float
    reasons: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _score(meta: Mapping[str, Any], figure_type: str, tags: set[str], role: str, query: Mapping[str, Any]) -> tuple[float, float, float, List[str]]:
    ftype = _norm(meta.get("figure_type"))
    target = _norm(figure_type)
    mtags = {_norm(x) for x in (meta.get("tags") or [])}
    grammar = meta.get("visual_grammar") or {}
    reasons: List[str] = []
    alignment = 0.0
    if role == "style_reference":
        # Style can cross figure families.  Favor explicit style metadata,
        # while treating an exact figure family as a modest bonus only.
        if ftype == target:
            alignment += 0.16
        if mtags & tags:
            alignment += 0.34
        if meta.get("journal_style") and query.get("journal_style") and _norm(meta.get("journal_style")) == _norm(query.get("journal_style")):
            alignment += 0.18
        if meta.get("style_spec_path") or meta.get("style_spec") or grammar.get("palette_roles"):
            alignment += 0.24
        if meta.get("layout") == query.get("layout"):
            alignment += 0.08
        reasons.append("style scored independently of figure family")
    else:
        if ftype == target:
            alignment += 0.55
            reasons.append("figure family matches")
        if mtags & tags:
            alignment += min(0.3, 0.12 * len(mtags & tags))
            reasons.append("retrieval tags overlap")
        if query.get("layout") and _norm(meta.get("layout")) == _norm(query["layout"]):
            alignment += 0.15
            reasons.append("layout matches")
        if query.get("subtype") and _norm(meta.get("subtype")) == _norm(query["subtype"]):
            alignment += 0.14
            reasons.append("subtype matches")
    aesthetic = float(meta.get("aesthetic_quality", meta.get("aesthetic_rating") or 0) or 0) / 5.0
    scientific = float(meta.get("scientific_correctness", meta.get("scientific_clarity") or (1.0 if ftype == target else 0.65)) or 0)
    if scientific > 1:
        scientific /= 5.0
    # Ineligible/unreviewed samples are not production references.
    if meta.get("review_status") not in {"reviewed", "promoted"}:
        alignment *= 0.25
        reasons.append("unreviewed: quarantined")
    return round(min(1.0, alignment), 4), round(min(1.0, aesthetic), 4), round(min(1.0, scientific), 4), reasons


class MultiRoleReferenceRetriever:
    """Retrieve independent reference roles from sidecar metadata.

    A candidate may be a style reference for a different chart family.  The
    returned scores intentionally remain separate; callers decide how to
    trade visual fit against aesthetics and scientific compatibility.
    """

    ROLES = ("structure_reference", "style_reference", "component_references", "annotation_reference", "palette_reference")

    def __init__(self, *, root: Optional[Path] = None, references: Optional[Iterable[Mapping[str, Any]]] = None):
        self.root = Path(root) if root else None
        if references is not None:
            self.references = [dict(x) for x in references]
        else:
            self.references = self._load_references()

    def _load_references(self) -> List[Dict[str, Any]]:
        # Prefer the existing sidecar source without importing the script as a
        # package.  This keeps the new runtime usable from both CLI and tests.
        root = self.root or Path(__file__).resolve().parents[4]
        ref_dir = root / "assets" / "visual-references"
        out: List[Dict[str, Any]] = []
        for path in ref_dir.glob("**/metadata.json"):
            try:
                meta = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            meta.setdefault("_metadata_path", path.as_posix())
            out.append(meta)
        return out

    def retrieve(self, *, figure_type: str, roles: Optional[Sequence[str]] = None, tags: Optional[Sequence[str]] = None, limit: int = 3, **query: Any) -> Dict[str, List[Dict[str, Any]]]:
        requested = list(roles or self.ROLES)
        tagset = {_norm(x) for x in (tags or [])}
        result: Dict[str, List[Dict[str, Any]]] = {}
        for role in requested:
            if role not in self.ROLES:
                raise ValueError(f"Unknown reference role: {role}")
            scored = []
            for meta in self.references:
                # Palette is a style-only role; annotation and component may
                # cross families but still require visual grammar evidence.
                if role != "style_reference" and role != "palette_reference" and not meta.get("visual_grammar") and not meta.get("layout"):
                    continue
                alignment, aesthetic, scientific, reasons = _score(meta, figure_type, tagset, role, query)
                if role == "palette_reference":
                    alignment = round((alignment + aesthetic) / 2, 4)
                scored.append(RoleMatch(
                    id=str(meta.get("id", "")), image_path=meta.get("image_path"), figure_type=str(meta.get("figure_type", "")), role=role,
                    reference_alignment_score=alignment, aesthetic_quality_score=aesthetic, scientific_correctness_score=scientific,
                    reasons=reasons, metadata=meta,
                ).to_dict())
            scored.sort(key=lambda x: (-x["reference_alignment_score"], -x["aesthetic_quality_score"], -x["scientific_correctness_score"], x["id"]))
            result[role] = scored[: max(1, int(limit))]
        return result


def retrieve_reference_roles(figure_type: str, *, root: Optional[Path] = None, references: Optional[Iterable[Mapping[str, Any]]] = None, **kwargs: Any) -> Dict[str, List[Dict[str, Any]]]:
    return MultiRoleReferenceRetriever(root=root, references=references).retrieve(figure_type=figure_type, **kwargs)
