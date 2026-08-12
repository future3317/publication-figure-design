# -*- coding: utf-8 -*-
"""Tests for the lightweight reference-fidelity process checker."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_reference_fidelity import validate_reference_fidelity


SCRIPT_MARKER = "# AFS-REFERENCE-DRIVEN: true\nprint('render')\n"


def make_contract(decision="rewrite", **overrides):
    must_match = ["2x2 panel topology", "marginal density layers"]
    contract = {
        "reference_source": "reference.png",
        "scientific_invariants": ["same variables", "all rows retained"],
        "canvas_layout": "2x2 compound layout",
        "mark_geometry": "scatter with marginal densities",
        "layer_topology": "scatter below regression and marginal layers",
        "data_encoding": "x/y position and group color",
        "palette_roles": "blue groups with orange accent",
        "typography": "compact sans-serif hierarchy",
        "legend_annotation": "external legend and direct regression labels",
        "spacing_hierarchy": "dense center, narrow marginal panels",
        "must_match": must_match,
        "may_adapt": [{"feature": "point positions", "reason": "user data differ"}],
        "implementation_decision": decision,
        "decision_evidence": "legacy plot has one panel and no marginal layers",
        "structural_compatibility": [],
        "structural_changes": ["replace one-axis layout with a 2x2 GridSpec", "add marginal density axes"],
        "fidelity_review": [
            {"feature": feature, "status": "pass", "reason": ""}
            for feature in must_match
        ],
    }
    contract.update(overrides)
    return contract


class TestReferenceFidelity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.comparison = Path(self.tmp.name) / "comparison.png"
        self.comparison.write_bytes(b"not-empty")

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_rewrite_is_ready(self):
        report = validate_reference_fidelity(SCRIPT_MARKER, make_contract(), self.comparison)
        self.assertTrue(report["ready"], report["errors"])

    def test_rewrite_rejects_cosmetic_only_changes(self):
        report = validate_reference_fidelity(
            SCRIPT_MARKER,
            make_contract(structural_changes=["change color", "increase font size", "set alpha"]),
            self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("cosmetic", " ".join(report["errors"]).lower())

    def test_rewrite_rejects_vague_nonstructural_changes(self):
        report = validate_reference_fidelity(
            SCRIPT_MARKER,
            make_contract(structural_changes=["refactor plotting code", "make it resemble the example"]),
            self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("structural", " ".join(report["errors"]).lower())

    def test_reuse_requires_structural_compatibility_evidence(self):
        report = validate_reference_fidelity(
            SCRIPT_MARKER,
            make_contract(decision="reuse", structural_changes=[], structural_compatibility=[]),
            self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("compatibility", " ".join(report["errors"]).lower())

    def test_unresolved_must_match_item_is_not_ready(self):
        review = [
            {"feature": "2x2 panel topology", "status": "pass", "reason": ""},
            {"feature": "marginal density layers", "status": "fail", "reason": ""},
        ]
        report = validate_reference_fidelity(
            SCRIPT_MARKER, make_contract(fidelity_review=review), self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("unresolved", " ".join(report["errors"]).lower())

    def test_justified_deviation_requires_reason(self):
        review = [
            {"feature": "2x2 panel topology", "status": "pass", "reason": ""},
            {"feature": "marginal density layers", "status": "justified_deviation", "reason": ""},
        ]
        report = validate_reference_fidelity(
            SCRIPT_MARKER, make_contract(fidelity_review=review), self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("reason", " ".join(report["errors"]).lower())

    def test_missing_comparison_is_not_ready(self):
        report = validate_reference_fidelity(
            SCRIPT_MARKER, make_contract(), Path(self.tmp.name) / "missing.png"
        )
        self.assertFalse(report["ready"])
        self.assertIn("comparison", " ".join(report["errors"]).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
