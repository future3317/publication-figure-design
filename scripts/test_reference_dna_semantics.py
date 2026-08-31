#!/usr/bin/env python3
"""Unit tests for ReferenceDNA 2.1 scientific-semantics inference."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from publication_figure_design.reference_intelligence.dna import ReferenceDNA


class ReferenceDNASemanticsTest(unittest.TestCase):
    def test_default_has_semantic_sections(self):
        dna = ReferenceDNA()
        for key in ("scientific_semantics", "encoding_rationale", "pedagogy", "caption_requirements", "accessibility_evidence"):
            self.assertIn(key, dna.to_dict())
            self.assertIsInstance(getattr(dna, key), dict)

    def test_infer_paired_relationship(self):
        meta = {"figure_type": "paired_operating_point"}
        dna = ReferenceDNA.from_metadata(meta)
        self.assertEqual(dna.scientific_semantics.get("data_relationship"), "paired")
        self.assertEqual(dna.scientific_semantics.get("paired_or_independent"), "paired")

    def test_infer_independent_bar(self):
        meta = {"figure_type": "GroupedBarChart"}
        dna = ReferenceDNA.from_metadata(meta)
        self.assertEqual(dna.scientific_semantics.get("data_relationship"), "independent_categorical")
        self.assertEqual(dna.encoding_rationale.get("primary_channel"), "position_aligned_length")

    def test_pedagogy_when_to_use(self):
        meta = {"figure_type": "paired_dot"}
        dna = ReferenceDNA.from_metadata(meta)
        self.assertIn("pair identity", dna.pedagogy.get("when_to_use", "").lower())

    def test_round_trip_through_json(self):
        dna = ReferenceDNA.from_metadata({"figure_type": "scatter_correlation"})
        payload = json.loads(json.dumps(dna.to_dict()))
        restored = ReferenceDNA(**payload)
        self.assertEqual(restored.scientific_semantics, dna.scientific_semantics)


if __name__ == "__main__":
    unittest.main()
