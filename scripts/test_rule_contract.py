# -*- coding: utf-8 -*-
"""Tests for the machine-readable rule hierarchy and evidence contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from check_rule_contract import validate_rules


ROOT = Path(__file__).resolve().parents[1]


class RuleContractTests(unittest.TestCase):
    def test_repository_rules_validate(self):
        report = validate_rules(ROOT)
        self.assertTrue(report["ok"], report["errors"])

    def test_block_rule_requires_verification_and_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules = root / "rules" / "global"
            rules.mkdir(parents=True)
            (root / "sources").mkdir()
            (root / "sources" / "registry.yaml").write_text("sources: []\n", encoding="utf-8")
            (rules / "bad.yaml").write_text(
                yaml.safe_dump(
                    {
                        "id": "BAD-001",
                        "title": "Missing evidence",
                        "scope": "global",
                        "severity": "block",
                        "statement": "A rule",
                        "verification": {"mode": "manual", "checks": []},
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            report = validate_rules(root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("source" in error.lower() for error in report["errors"]))

    def test_duplicate_rule_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules = root / "rules" / "house"
            rules.mkdir(parents=True)
            (root / "sources").mkdir()
            (root / "sources" / "registry.yaml").write_text("sources: []\n", encoding="utf-8")
            payload = {
                "id": "HOUSE-001",
                "title": "Duplicate",
                "scope": "house",
                "severity": "advisory",
                "statement": "A rule",
                "verification": {"mode": "manual", "checks": ["review"]},
                "evidence": [],
            }
            for name in ("one.yaml", "two.yaml"):
                (rules / name).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            report = validate_rules(root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("duplicate" in error.lower() for error in report["errors"]))

    def test_unknown_conflict_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules = root / "rules" / "global"
            rules.mkdir(parents=True)
            (root / "sources").mkdir()
            (root / "sources" / "registry.yaml").write_text("sources: []\n", encoding="utf-8")
            (rules / "conflict.yaml").write_text(
                yaml.safe_dump({
                    "id": "GLOB-001", "title": "Conflict", "scope": "global", "severity": "warn",
                    "statement": "A rule", "conflicts_with": ["MISSING-001"],
                    "verification": {"mode": "manual", "checks": ["review"]}, "evidence": [],
                }, sort_keys=False), encoding="utf-8"
            )
            report = validate_rules(root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("conflicts_with" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
