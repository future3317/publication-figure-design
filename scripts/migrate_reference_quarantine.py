#!/usr/bin/env python3
"""Attach the explicit quarantine lifecycle to legacy sidecars.

Migration preserves existing review decisions.  Reviewed legacy references are
marked ``benchmarked`` with a provenance note pointing to the already recorded
reconstruction/fidelity evidence; they are not silently promoted to production.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def migrate(root: Path, *, apply: bool = False) -> dict:
    changed = 0
    for path in sorted((root / "assets" / "visual-references").glob("**/metadata.json")):
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if metadata.get("lifecycle_state"):
            continue
        review_status = metadata.get("review_status", "pending")
        if review_status in {"reviewed", "promoted"}:
            state = "benchmarked"
            history = [{"state": "benchmarked", "reason": "legacy_reviewed_corpus_migration", "evidence": "existing reconstruction/fidelity review artifacts"}]
        elif review_status == "rejected":
            state = "rejected"
            history = [{"state": "rejected", "reason": "legacy_review_status"}]
        else:
            state = "raw"
            history = [{"state": "raw", "reason": "legacy_intake_migration"}]
        metadata["lifecycle_state"] = state
        metadata["quarantine"] = {"state": state, "history": history}
        changed += 1
        if apply:
            path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return {"changed": changed, "applied": apply}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(migrate(root, apply=args.apply), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
