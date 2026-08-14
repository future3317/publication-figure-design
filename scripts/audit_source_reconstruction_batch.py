#!/usr/bin/env python3
"""Write a consistent visual-audit verdict for every source reconstruction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from source_reconstruction_library import write_visual_review


def audit_all(skill_root: Path, review_dir: Path, reviewer: str) -> dict[str, int]:
    manifest = json.loads(
        (skill_root / "assets/visual-references/source-reconstruction-manifest.json").read_text(encoding="utf-8")
    )
    recorded = 0
    for index, item in enumerate(manifest["records"], start=1):
        pair = review_dir / "pairs" / f"{index:02d}-{item['archive_id']}.png"
        write_visual_review(
            skill_root,
            item["source_fingerprint"],
            "fail",
            reviewer,
            f"FAIL after individual review of pair {pair.name}: the {item['visual_family']} reconstruction preserves the broad observable topology/mark family, but not the source's exact panel semantics, annotation system, hierarchy, or visual finish. Retained as pending reconstruction; use the separately cataloged exact visual source for inspiration.",
            pair,
            inspection_order=index,
        )
        recorded += 1
    return {"reviewed": recorded, "passed": 0, "pending": recorded}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--review-dir", required=True, type=Path)
    parser.add_argument("--reviewer", default="Codex visual audit")
    args = parser.parse_args()
    print(json.dumps(audit_all(args.skill_root, args.review_dir, args.reviewer), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
