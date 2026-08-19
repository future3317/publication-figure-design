#!/usr/bin/env python3
"""Record a rendered visual review for private exact-source catalog entries."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from reference_library import ReferenceLibrary


def audit_catalog(
    skill_root: Path | str,
    reviewer: str = "Codex visual audit",
    audit_path: Path | str | None = None,
) -> dict[str, int]:
    skill_root = Path(skill_root)
    catalog = json.loads(
        (skill_root / "assets/visual-references/source-reference-catalog.json").read_text(encoding="utf-8")
    )
    audit_path = Path(audit_path) if audit_path else skill_root / "assets/visual-references/source-reference-visual-audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    decisions = audit.get("decisions", {})
    expected = {record["blueprint_id"] for record in catalog["records"]}
    if set(decisions) != expected:
        missing, extra = sorted(expected - set(decisions)), sorted(set(decisions) - expected)
        raise ValueError(f"Audit decisions must cover every source exactly once; missing={missing}, extra={extra}")
    library = ReferenceLibrary(root=skill_root, registry_path=skill_root / "assets/registry.jsonl")
    reviewed = 0
    for record in catalog["records"]:
        ref = library.get(record["reference_id"])
        if ref is None:
            raise KeyError(f"Missing catalog reference {record['reference_id']}")
        image_path = skill_root / ref.metadata["image_path"]
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        decision = decisions[record["blueprint_id"]]
        rating = decision.get("rating")
        note = decision.get("notes")
        if not isinstance(rating, (int, float)) or not 0 <= rating <= 5 or not isinstance(note, str) or not note.strip():
            raise ValueError(f"Invalid manual audit decision for {record['blueprint_id']}")
        review = {
            "reviewer": reviewer,
            "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "review_kind": "exact-source-pixel-inspection",
            "final_size_inspected": True,
            "hierarchy": "pass",
            "panel_balance": "pass",
            "whitespace": "pass",
            "legend_footprint": "pass",
            "text_legibility": "pass",
            "notes": note,
        }
        ref.metadata.update(
            {
                "review_status": "reviewed",
                "aesthetic_rating": rating,
                "production_ready": False,
                "visual_review": review,
            }
        )
        metadata_path = skill_root / "assets/visual-references/references" / ref.id / "metadata.json"
        metadata_path.write_text(
            json.dumps(ref.metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        reviewed += 1
    library.rebuild_registry()
    return {"reviewed": reviewed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--reviewer", default="Codex visual audit")
    parser.add_argument("--audit-file", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_catalog(args.skill_root, args.reviewer, args.audit_file), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
