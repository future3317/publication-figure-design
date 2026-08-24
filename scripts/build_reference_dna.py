#!/usr/bin/env python3
"""Build ReferenceDNA sidecars for the current reference collection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from publication_figure_design.reference_intelligence.dna_builder import build_reference_dna  # noqa: E402


def build_all(root: Path = ROOT) -> dict[str, int]:
    built = 0
    failures = 0
    for metadata_path in sorted((root / "assets" / "visual-references").glob("**/metadata.json")):
        try:
            build_one(metadata_path.parent, root=root)
            built += 1
        except (OSError, ValueError, SyntaxError, ImportError):
            failures += 1
    return {"built": built, "failures": failures}


def build_one(reference_dir: Path, *, root: Path = ROOT) -> dict[str, int]:
    """Build one DNA sidecar and persist its metadata pointer/state."""
    root = Path(root).resolve()
    reference_dir = Path(reference_dir).resolve()
    build_reference_dna(reference_dir)
    metadata_path = reference_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    dna_path = reference_dir / "reference_dna.json"
    metadata["reference_dna_path"] = dna_path.relative_to(root).as_posix()
    figure_card_path = reference_dir / "figure_card.json"
    if figure_card_path.is_file():
        metadata["figure_card_path"] = figure_card_path.relative_to(root).as_posix()
    if metadata.get("lifecycle_state") == "raw":
        metadata["lifecycle_state"] = "analyzed"
        metadata.setdefault("quarantine", {"state": "raw", "history": []})
        metadata["quarantine"]["state"] = "analyzed"
        history = metadata["quarantine"].setdefault("history", [])
        if not any(
            item.get("state") == "analyzed" and item.get("reason") == "reference_dna_built"
            for item in history if isinstance(item, dict)
        ):
            history.append({"state": "analyzed", "reason": "reference_dna_built"})
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"built": 1, "failures": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path)
    args = parser.parse_args()
    report = build_one(args.reference_dir) if args.reference_dir else build_all()
    print(json.dumps(report.to_dict() if hasattr(report, "to_dict") else report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
