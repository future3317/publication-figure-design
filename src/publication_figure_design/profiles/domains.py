"""Domain profile loader for publication-figure-design."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[3]
PROFILE_DIR = ROOT / "profiles" / "domains"
SCHEMA_PATH = ROOT / "schemas" / "domain-profile.schema.json"


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(profile: Mapping[str, Any]) -> list[str]:
    """Minimal structural validation against the domain profile schema."""
    errors: list[str] = []
    schema = _schema()
    required = schema.get("required", [])
    for key in required:
        if key not in profile:
            errors.append(f"missing required field: {key}")
    status = profile.get("status")
    if status not in {"verified", "stale", "placeholder"}:
        errors.append(f"invalid status: {status!r}")
    confidence = profile.get("confidence")
    if confidence not in {"authoritative", "inferred"}:
        errors.append(f"invalid confidence: {confidence!r}")
    return errors


def load_domain_profile(domain: str) -> dict[str, Any]:
    """Load and validate a domain profile by domain identifier."""
    path = PROFILE_DIR / domain / "profile.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"domain profile not found: {path}")
    profile = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = _validate(profile)
    if errors:
        raise ValueError(f"invalid domain profile {domain}: {errors}")
    profile["domain"] = domain
    return dict(profile)


def list_domains() -> list[str]:
    """List available domain identifiers."""
    if not PROFILE_DIR.is_dir():
        return []
    return sorted(
        p.name for p in PROFILE_DIR.iterdir()
        if p.is_dir() and (p / "profile.yaml").is_file()
    )


def load_all() -> dict[str, dict[str, Any]]:
    """Load all domain profiles."""
    return {domain: load_domain_profile(domain) for domain in list_domains()}
