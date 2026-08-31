#!/usr/bin/env python3
"""Unit tests for the output eval runner."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from run_output_eval import run_suite  # type: ignore


class OutputEvalRunnerTest(unittest.TestCase):
    def test_adversarial_suite_runs(self):
        suite_dir = ROOT / "evals" / "adversarial-mutations"
        report = run_suite(suite_dir)
        self.assertEqual(report["suite"], "adversarial-mutations")
        self.assertEqual(report["task_count"], 12)
        self.assertIn("precision", report)
        self.assertIn("recall", report)
        self.assertIn("f1", report)
        for case in report["cases"]:
            self.assertIn("expected_failures", case)
            self.assertIn("detected_failures", case)

    def test_expected_rules_exist(self):
        suite_dir = ROOT / "evals" / "adversarial-mutations"
        report = run_suite(suite_dir)
        for case in report["cases"]:
            self.assertTrue(
                all(rule in self._rule_ids() for rule in case["expected_failures"]),
                f"{case['id']} references unknown rule",
            )

    def _rule_ids(self):
        import yaml
        ids = set()
        for path in sorted((ROOT / "rules").rglob("*.yaml")):
            if path.name == "_index.yaml":
                continue
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            rules = payload.get("rules", payload if isinstance(payload, list) else [])
            for rule in rules:
                if isinstance(rule, dict) and rule.get("id"):
                    ids.add(str(rule["id"]))
        return ids


if __name__ == "__main__":
    unittest.main()
