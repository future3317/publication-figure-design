"""Versioned journal profile loader with explicit rule levels."""

from __future__ import annotations

from pathlib import Path

import yaml

from ..reference_intelligence.dna import JournalProfile


ROOT = Path(__file__).resolve().parents[3]


def load_journal_profile(name: str, stage: str = "final_submission", *, root: Path = ROOT) -> JournalProfile:
    journal = name.lower().replace(" ", "_")
    path = root / "profiles" / "journals" / journal / f"{stage}.yaml"
    if not path.is_file():
        path = root / "profiles" / "journals" / "generic.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return JournalProfile(name=str(payload.get("name", journal)), stage=str(payload.get("stage", stage)), rules=dict(payload.get("rules", {})), source=str(payload.get("source", "")), source_date=str(payload.get("source_date", "")))
