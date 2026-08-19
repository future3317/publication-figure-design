#!/usr/bin/env python3
"""Measure retrieval stability at the supported reference-library sizes."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication_figure_design.references.retrieval.multi_role import MultiRoleReferenceRetriever


SIZES = (100, 500, 1000, 5000)


def run() -> dict:
    reports = []
    for size in SIZES:
        refs = [
            {
                "id": f"ref-{index}",
                "figure_type": "grouped_bar" if index % 2 == 0 else "scatter_bubble",
                "review_status": "reviewed",
                "lifecycle_state": "benchmarked",
                "tags": ["minimal" if index % 3 else "nature"],
                "layout": "wide",
                "visual_grammar": {"palette_roles": {"accent": "#123456"}},
                "aesthetic_rating": 3.0 + (index % 20) / 10,
                "sha256": f"digest-{index}",
            }
            for index in range(size)
        ]
        start = time.perf_counter()
        result = MultiRoleReferenceRetriever(references=refs).retrieve(
            figure_type="grouped_bar", roles=("structure_reference", "style_reference"), tags=("minimal",), limit=3
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        ids = [row["id"] for row in result["structure_reference"]]
        reports.append({"size": size, "latency_ms": round(elapsed_ms, 3), "recall_at_1": float(bool(ids and ids[0].startswith("ref-"))), "duplicate_count": len(ids) - len(set(ids))})
    failures = [f"duplicate results at size {row['size']}" for row in reports if row["duplicate_count"]]
    return {"sizes": reports, "failures": failures, "passed": not failures}


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["passed"] else 1)
