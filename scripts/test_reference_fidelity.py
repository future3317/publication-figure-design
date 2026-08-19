# -*- coding: utf-8 -*-
"""Tests for the lightweight reference-fidelity process checker."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from check_reference_fidelity import validate_reference_fidelity


def script_marker(level="build_new"):
    return f"# AFS-REFERENCE-DRIVEN: true\n# AFS-ADAPTATION-LEVEL: {level}\nprint('render')\n"


def visual_grammar():
    return {
        "canvas_composition": {
            "aspect_and_panel_layout": "wide 2x2 compound layout with narrow marginal panels",
            "visual_hierarchy": "central scatter panel is dominant; marginals are supporting evidence",
            "alignment_and_spacing": "axes align to the central panel with compact internal gutters",
        },
        "connectors": "not_present",
        "objects_material": "not_present",
        "repetition_structures": "not_present",
        "palette_roles": {
            "background": "white canvas with pale gray guides",
            "roles_and_proportions": "blue groups dominate with a small orange accent",
            "contrast_and_emphasis": "dark marks carry evidence; guides remain subordinate",
        },
        "annotations_typography": {
            "text_hierarchy": "compact sans-serif labels with a heavier panel title",
            "callouts_and_leaders": "direct regression labels; no leader lines",
            "placement_and_clearance": "labels sit in unused plot corners",
        },
        "legend_key": {
            "scope": "global key for group colors",
            "placement": "outside the data region",
            "entries_and_encoding": "one colored symbol per group",
            "frame_treatment": "no enclosing box",
        },
        "chart_marks_axes": {
            "marks_and_encoding": "points use x/y position and group color",
            "axes_and_scales": "linear x/y scales with marginal densities",
            "guides_and_grid": "minimal light-gray guide lines",
        },
        "must_match": ["2x2 panel topology", "marginal density layers"],
    }


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
        "reference_visual_grammar": visual_grammar(),
        "must_match": must_match,
        "may_adapt": [{"feature": "point positions", "reason": "user data differ"}],
        "implementation_decision": decision,
        "adaptation_level": {
            "reuse": "exact_reuse",
            "restructure": "structural_adaptation",
            "rewrite": "build_new",
        }[decision],
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
        self.reference = Path(self.tmp.name) / "reference.png"
        self.candidate = Path(self.tmp.name) / "candidate.png"
        Image.new("RGB", (40, 30), "white").save(self.reference)
        Image.new("RGB", (40, 30), "#eeeeee").save(self.candidate)
        comparison = Image.new("RGB", (80, 30), "white")
        comparison.paste(Image.open(self.reference), (0, 0))
        comparison.paste(Image.open(self.candidate), (40, 0))
        comparison.save(self.comparison)

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_rewrite_is_ready(self):
        report = validate_reference_fidelity(
            script_marker(), make_contract(), self.comparison, self.reference, self.candidate
        )
        self.assertTrue(report["ready"], report["errors"])

    def test_visual_grammar_observation_is_required(self):
        value = make_contract()
        value.pop("reference_visual_grammar")
        report = validate_reference_fidelity(
            script_marker(), value, self.comparison, self.reference, self.candidate
        )
        self.assertFalse(report["ready"])
        self.assertIn("visual grammar", " ".join(report["errors"]).lower())

    def test_present_connectors_need_geometry_stroke_and_routing_details(self):
        value = make_contract()
        value["reference_visual_grammar"]["connectors"] = {"geometry": "curved arrows"}
        report = validate_reference_fidelity(
            script_marker(), value, self.comparison, self.reference, self.candidate
        )
        self.assertFalse(report["ready"])
        self.assertIn("connectors", " ".join(report["errors"]).lower())

    def test_rewrite_rejects_cosmetic_only_changes(self):
        report = validate_reference_fidelity(
            script_marker(),
            make_contract(structural_changes=["change color", "increase font size", "set alpha"]),
            self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("cosmetic", " ".join(report["errors"]).lower())

    def test_rewrite_rejects_vague_nonstructural_changes(self):
        report = validate_reference_fidelity(
            script_marker(),
            make_contract(structural_changes=["refactor plotting code", "make it resemble the example"]),
            self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("structural", " ".join(report["errors"]).lower())

    def test_reuse_requires_structural_compatibility_evidence(self):
        report = validate_reference_fidelity(
            script_marker("exact_reuse"),
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
            script_marker(), make_contract(fidelity_review=review), self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("unresolved", " ".join(report["errors"]).lower())

    def test_justified_deviation_requires_reason(self):
        review = [
            {"feature": "2x2 panel topology", "status": "pass", "reason": ""},
            {"feature": "marginal density layers", "status": "justified_deviation", "reason": ""},
        ]
        report = validate_reference_fidelity(
            script_marker(), make_contract(fidelity_review=review), self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("reason", " ".join(report["errors"]).lower())

    def test_missing_comparison_is_not_ready(self):
        report = validate_reference_fidelity(
            script_marker(), make_contract(), Path(self.tmp.name) / "missing.png"
        )
        self.assertFalse(report["ready"])
        self.assertIn("comparison", " ".join(report["errors"]).lower())

    def test_non_image_comparison_is_not_ready(self):
        fake = Path(self.tmp.name) / "fake.png"
        fake.write_bytes(b"not-an-image")
        report = validate_reference_fidelity(script_marker(), make_contract(), fake)
        self.assertFalse(report["ready"])
        self.assertIn("image", " ".join(report["errors"]).lower())

    def test_comparison_must_contain_reference_and_candidate(self):
        unrelated = Path(self.tmp.name) / "unrelated.png"
        Image.new("RGB", (80, 30), "red").save(unrelated)
        report = validate_reference_fidelity(
            script_marker(), make_contract(), unrelated, self.reference, self.candidate
        )
        self.assertFalse(report["ready"])
        self.assertIn("contain", " ".join(report["errors"]).lower())

    def test_reuse_requires_exact_reuse_level(self):
        report = validate_reference_fidelity(
            script_marker("style_only"),
            make_contract(
                decision="reuse",
                adaptation_level="style_only",
                structural_changes=[],
                structural_compatibility=["topology", "marks", "layers", "encoding", "legend"],
            ),
            self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("adaptation", " ".join(report["errors"]).lower())

    def test_rewrite_accepts_style_only_when_compatible_tokens_remain(self):
        report = validate_reference_fidelity(
            script_marker("style_only"),
            make_contract(adaptation_level="style_only"),
            self.comparison,
            self.reference,
            self.candidate,
        )
        self.assertTrue(report["ready"], report["errors"])

    def test_comparison_requires_both_source_images(self):
        report = validate_reference_fidelity(script_marker(), make_contract(), self.comparison)
        self.assertFalse(report["ready"])
        self.assertIn("source images", " ".join(report["errors"]).lower())

    def test_adaptation_marker_must_match_contract(self):
        report = validate_reference_fidelity(
            script_marker("style_only"), make_contract(), self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("marker", " ".join(report["errors"]).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
