#!/usr/bin/env python3
"""Adversarial role-separation checks for reference retrieval."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication_figure_design.references.retrieval.multi_role import MultiRoleReferenceRetriever


def run() -> dict:
    refs = [
        {"id": "structure-good", "figure_type": "grouped_bar", "review_status": "reviewed", "lifecycle_state": "benchmarked", "tags": ["minimal"], "layout": "wide", "visual_grammar": {"repetition_structures": {"topology": "bars"}}, "aesthetic_rating": 4.0, "sha256": "a"},
        {"id": "style-good", "figure_type": "scatter_bubble", "review_status": "reviewed", "lifecycle_state": "benchmarked", "tags": ["minimal", "nature"], "layout": "wide", "visual_grammar": {"palette_roles": {"ours": "#123456"}}, "aesthetic_rating": 5.0, "sha256": "b"},
        {"id": "high-aesthetic-wrong-structure", "figure_type": "scatter_bubble", "review_status": "reviewed", "lifecycle_state": "benchmarked", "tags": ["minimal"], "layout": "wide", "visual_grammar": {"palette_roles": {"ours": "#abcdef"}}, "aesthetic_rating": 5.0, "sha256": "c"},
        {"id": "structure-correct-aesthetic-poor", "figure_type": "grouped_bar", "review_status": "reviewed", "lifecycle_state": "benchmarked", "tags": ["minimal"], "layout": "wide", "visual_grammar": {"repetition_structures": {"topology": "bars"}}, "aesthetic_rating": 1.0, "sha256": "d"},
        {"id": "near-duplicate", "figure_type": "grouped_bar", "review_status": "reviewed", "lifecycle_state": "benchmarked", "tags": ["misleading"], "layout": "wide", "visual_grammar": {"repetition_structures": {"topology": "bars"}}, "aesthetic_rating": 5.0, "sha256": "a"},
        {"id": "quarantined", "figure_type": "grouped_bar", "review_status": "reviewed", "lifecycle_state": "analyzed", "tags": ["minimal"], "layout": "wide", "visual_grammar": {"repetition_structures": {"topology": "bars"}}, "aesthetic_rating": 5.0, "sha256": "e"},
    ]
    retriever = MultiRoleReferenceRetriever(references=refs)
    result = retriever.retrieve(figure_type="grouped_bar", roles=("structure_reference",), tags=("minimal",), layout="wide", limit=3)
    style_result = retriever.retrieve(figure_type="grouped_bar", roles=("style_reference",), tags=("nature",), layout="wide", limit=3)
    failures: list[str] = []
    structure_ids = [row["id"] for row in result["structure_reference"]]
    style_ids = [row["id"] for row in style_result["style_reference"]]
    if structure_ids[:1] != ["structure-good"]:
        failures.append(f"structure retrieval was not led by exact structure: {structure_ids}")
    if "quarantined" in structure_ids:
        failures.append("quarantined reference entered retrieval")
    if len(structure_ids) != len(set(structure_ids)):
        failures.append("near duplicate was returned twice")
    if not style_ids or style_ids[0] not in {"style-good", "structure-good"}:
        failures.append(f"style retrieval lost cross-family style candidate: {style_ids}")
    return {"cases": ["wrong metadata", "aesthetic/structure conflict", "near duplicate", "cross-family style", "misleading tags", "quarantine"], "failures": failures, "passed": not failures}


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["passed"] else 1)
