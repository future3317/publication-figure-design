# -*- coding: utf-8 -*-
from __future__ import annotations

import tempfile
import unittest
import hashlib
from pathlib import Path

from PIL import Image

from scripts.check_visual_optimization import validate_visual_optimization


def contract(**overrides):
    recommendation = {
        "status": "insufficient_pool",
        "request": {"figure_type": "line_trend"},
        "candidates": [{
            "id": "reviewed-ref-1", "figure_type": "line_trend",
            "image_sha256": None, "matches": ["Exact figure type"], "cautions": []
        }],
    }
    value = {
        "task": "visual_optimization",
        "reference_candidates": ["reviewed-ref-1"],
        "opened_reference_candidates": ["reviewed-ref-1"],
        "selected_reference": "reviewed-ref-1",
        "candidate_recommendation": recommendation,
        "candidate_pixel_observations": {
            "reviewed-ref-1": "direct labels and a hero/support panel hierarchy are visible"
        },
        "selection_reason": "best structural match for the hero/support evidence chain",
        "palette_decision": {
            "previous_palette": ["#8DBAD5", "#153E75"],
            "selected_palette": "journal_baseline",
            "semantic_mapping": {"matched": "#2166AC", "mismatched": "#999999"},
            "reason": "Blue is reserved for matched learners and grey for mismatched context.",
        },
        "art_direction": {
            "id": "hero_illustration",
            "reason": "A single geometric hero and progressive explanation best serve the mechanism claim.",
        },
        "series_encoding_contract": {
            "method_style_map": {
                "Delta-Hull": {"color": "#2166AC", "linestyle": "-", "marker": "o"},
                "reference": {"color": "#999999", "linestyle": "--", "marker": "^"},
            },
            "panel_series": {"a": ["Delta-Hull", "reference"], "b": ["Delta-Hull"]},
            "legend_scope": "global",
            "same_series_style_invariant": True,
            "unresolved_orphan_series": [],
        },
        "uncertainty_contract": {
            "interval_definition": "not_applicable",
            "overlap_strategy": "not_applicable",
            "alpha": None,
        },
        "text_contrast": {"applicable": False},
        "before_diagnosis": ["equal panels obscure the hero result", "legend dominates data"],
        "structural_changes": ["replace equal grid with a 2:1 hero/support GridSpec", "direct-label key curves and remove legend"],
        "composition_decision": {
            "old_skeleton_removed": True,
            "hero_panel": "paired score interval is the dominant panel",
            "support_panels": "three repaired diagnostics are compact comparison cards",
        },
        "visual_review": {
            "final_size_inspected": True,
            "hierarchy": "pass",
            "panel_balance": "pass",
            "whitespace": "pass",
            "legend_footprint": "pass",
            "text_legibility": "pass",
            "cross_panel_semantics": "pass",
            "legend_data_separation": "pass",
            "uncertainty_legibility": "pass",
            "axis_label_compactness": "pass",
        },
        "final_render": {
            "width_mm": 4.23,
            "height_mm": 3.39,
            "dpi": 300,
            "tolerance_mm": 0.1,
        },
    }
    value.update(overrides)
    return value


class VisualOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.before = root / "before.png"
        self.after = root / "after.png"
        self.reference = root / "reference.png"
        self.comparison = root / "comparison.png"
        Image.new("RGB", (50, 40), "white").save(self.before)
        Image.new("RGB", (50, 40), "#dddddd").save(self.after)
        Image.new("RGB", (50, 40), "#eeeeee").save(self.reference)
        canvas = Image.new("RGB", (150, 40), "white")
        for index, path in enumerate((self.before, self.reference, self.after)):
            with Image.open(path) as image:
                canvas.paste(image, (index * 50, 0))
        canvas.save(self.comparison)
        self.reference_sha256 = hashlib.sha256(self.reference.read_bytes()).hexdigest()

    def valid_contract(self, **overrides):
        value = contract()
        value["candidate_recommendation"]["candidates"][0]["image_sha256"] = self.reference_sha256
        value.update(overrides)
        return value

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_structural_optimization_is_ready(self):
        report = validate_visual_optimization(
            self.valid_contract(), self.before, self.after, self.reference, self.comparison
        )
        self.assertTrue(report["ready"], report["errors"])

    def test_palette_decision_is_required_even_when_old_colors_are_kept(self):
        value = self.valid_contract()
        del value["palette_decision"]
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("palette", " ".join(report["errors"]).lower())

    def test_art_direction_must_be_selected_and_justified(self):
        value = self.valid_contract()
        value.pop("art_direction")
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("art direction", " ".join(report["errors"]).lower())

        value = self.valid_contract(art_direction={"id": "unselected", "reason": ""})
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("art direction", " ".join(report["errors"]).lower())

    def test_text_on_fill_requires_a_passing_rendered_contrast_report(self):
        value = self.valid_contract(text_contrast={"applicable": True})
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("contrast", " ".join(report["errors"]).lower())

    def test_passing_rendered_contrast_report_allows_text_on_fill(self):
        from PIL import ImageDraw
        with Image.open(self.after) as image:
            image = image.convert("RGB")
            ImageDraw.Draw(image).text((5, 5), "ink", fill="#222222")
            image.save(self.after)
        from scripts.visual_evidence import compose_equal_size_comparison
        compose_equal_size_comparison((self.before, self.reference, self.after), self.comparison)
        value = self.valid_contract(text_contrast={
            "applicable": True,
            "report": {"ready": True, "minimum_ratio": 4.5, "regions": [{"region": [0, 0, 30, 20], "pass": True, "contrast_ratio": 5.1}]},
        })
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison
        )
        self.assertTrue(report["ready"], report["errors"])

    def test_cosmetic_only_changes_fail(self):
        report = validate_visual_optimization(
            self.valid_contract(structural_changes=["change colors", "increase font size", "reduce alpha"]),
            self.before, self.after, self.reference, self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("cosmetic", " ".join(report["errors"]).lower())

    def test_reference_must_have_been_opened(self):
        report = validate_visual_optimization(
            self.valid_contract(opened_reference_candidates=[]),
            self.before, self.after, self.reference, self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("opened", " ".join(report["errors"]).lower())

    def test_recommendation_report_is_required(self):
        report = validate_visual_optimization(
            self.valid_contract(candidate_recommendation={}),
            self.before, self.after, self.reference, self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("recommendation", " ".join(report["errors"]).lower())

    def test_candidate_ids_must_match_recommendation_report(self):
        bad = self.valid_contract()
        bad["candidate_recommendation"]["candidates"] = [{"id": "different-ref"}]
        report = validate_visual_optimization(
            bad, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("candidate ids", " ".join(report["errors"]).lower())

    def test_every_candidate_needs_pixel_observation(self):
        report = validate_visual_optimization(
            self.valid_contract(candidate_pixel_observations={}),
            self.before, self.after, self.reference, self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("pixel observation", " ".join(report["errors"]).lower())

    def test_comparison_must_contain_all_three_images(self):
        unrelated = Path(self.tmp.name) / "unrelated.png"
        Image.new("RGB", (150, 40), "red").save(unrelated)
        report = validate_visual_optimization(
            self.valid_contract(), self.before, self.after, self.reference, unrelated
        )
        self.assertFalse(report["ready"])
        self.assertIn("contain", " ".join(report["errors"]).lower())

    def test_final_size_review_is_mandatory(self):
        report = validate_visual_optimization(
            self.valid_contract(visual_review={"final_size_inspected": False}),
            self.before, self.after, self.reference, self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("final", " ".join(report["errors"]).lower())

    def test_before_and_after_must_visibly_differ(self):
        report = validate_visual_optimization(
            self.valid_contract(), self.before, self.before, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("differ", " ".join(report["errors"]).lower())

    def test_legend_color_change_is_still_cosmetic(self):
        report = validate_visual_optimization(
            self.valid_contract(structural_changes=["change legend colors and font size"]),
            self.before, self.after, self.reference, self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("cosmetic", " ".join(report["errors"]).lower())

    def test_old_equal_weight_skeleton_must_be_explicitly_rejected(self):
        value = self.valid_contract()
        del value["composition_decision"]
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("old figure skeleton", " ".join(report["errors"]).lower())

    def test_contrast_report_must_be_recomputed_for_after_image(self):
        value = self.valid_contract(text_contrast={
            "applicable": True,
            "report": {
                "ready": True, "minimum_ratio": 4.5,
                "regions": [{"region": [0, 0, 10, 10], "pass": True, "contrast_ratio": 21.0}],
            },
        })
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("recomputed", " ".join(report["errors"]).lower())

    def test_final_render_dimensions_are_required(self):
        value = self.valid_contract()
        del value["final_render"]
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison,
        )
        self.assertFalse(report["ready"])
        self.assertIn("physical", " ".join(report["errors"]).lower())

    def test_selected_reference_pixels_must_match_report_hash(self):
        bad = self.valid_contract()
        bad["candidate_recommendation"]["candidates"][0]["image_sha256"] = "0" * 64
        report = validate_visual_optimization(
            bad, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("sha-256", " ".join(report["errors"]).lower())

    def test_every_recommended_candidate_must_be_opened(self):
        value = self.valid_contract()
        value["reference_candidates"] = ["reviewed-ref-1", "reviewed-ref-2"]
        value["candidate_recommendation"]["candidates"].append({
            "id": "reviewed-ref-2", "figure_type": "line_trend",
            "image_sha256": "1" * 64, "matches": ["Exact figure type"], "cautions": []
        })
        value["candidate_pixel_observations"]["reviewed-ref-2"] = "faceted layout"
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("every recommended candidate", " ".join(report["errors"]).lower())

    def test_cross_panel_semantics_and_uncertainty_contract_are_required(self):
        value = self.valid_contract()
        value.pop("series_encoding_contract", None)
        value.pop("uncertainty_contract", None)
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        errors = " ".join(report["errors"]).lower()
        self.assertIn("cross-panel", errors)
        self.assertIn("uncertainty", errors)

    def test_unresolved_orphan_series_fails(self):
        value = self.valid_contract()
        value["series_encoding_contract"]["unresolved_orphan_series"] = ["panel d purple line"]
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("orphan", " ".join(report["errors"]).lower())

    def test_overlapping_uncertainty_alpha_is_bounded(self):
        value = self.valid_contract()
        value["uncertainty_contract"]["alpha"] = 0.8
        report = validate_visual_optimization(
            value, self.before, self.after, self.reference, self.comparison
        )
        self.assertFalse(report["ready"])
        self.assertIn("uncertainty", " ".join(report["errors"]).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
