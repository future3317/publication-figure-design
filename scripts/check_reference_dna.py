#!/usr/bin/env python3
"""Validate ReferenceDNA coverage and source-specific confidence contracts."""

from __future__ import annotations

import json
from pathlib import Path


def check(root: Path) -> dict:
    references = list((root / "assets" / "visual-references").glob("**/metadata.json"))
    missing: list[str] = []
    invalid: list[str] = []
    for metadata_path in references:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        dna_path = metadata_path.parent / "reference_dna.json"
        if not dna_path.is_file():
            missing.append(str(metadata_path.parent))
            continue
        if metadata.get("reference_dna_path") != dna_path.relative_to(root).as_posix():
            invalid.append(f"{metadata_path}: reference_dna_path does not point to sidecar")
        dna = json.loads(dna_path.read_text(encoding="utf-8"))
        if dna.get("schema_version") != "2.0" or not all(isinstance(dna.get(key), dict) for key in ("identity", "composition", "palette", "typography", "geometry", "annotations", "hierarchy", "style", "constraints", "confidence")):
            invalid.append(str(dna_path))
    return {"references": len(references), "missing": missing, "invalid": invalid, "passed": not missing and not invalid}


def main() -> int:
    report = check(Path(__file__).resolve().parents[1])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
