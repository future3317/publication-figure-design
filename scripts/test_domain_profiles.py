#!/usr/bin/env python3
"""Unit tests for domain profile loader and schema."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from publication_figure_design.profiles.domains import list_domains, load_all, load_domain_profile


class DomainProfileTest(unittest.TestCase):
    def test_list_domains(self):
        domains = list_domains()
        self.assertIn("ml-ai", domains)
        self.assertIn("biomedical", domains)
        self.assertIn("genomics", domains)
        self.assertIn("microscopy", domains)

    def test_load_ml_ai(self):
        profile = load_domain_profile("ml-ai")
        self.assertEqual(profile["name"], "Machine Learning and AI")
        self.assertIn("classification_diagnostics", profile["preferred_families"])
        self.assertIn("tripod-ai", profile.get("reporting_standards", []))

    def test_load_all_valid(self):
        profiles = load_all()
        self.assertGreaterEqual(len(profiles), 4)
        for domain, profile in profiles.items():
            self.assertEqual(profile["domain"], domain)
            self.assertIn("preferred_families", profile)

    def test_schema_exists(self):
        schema_path = ROOT / "schemas" / "domain-profile.schema.json"
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertIn("required", schema)


if __name__ == "__main__":
    unittest.main()
