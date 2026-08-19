# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from scripts.figure_family_coverage import FIGURE_FAMILIES, build_coverage_report
from scripts.reference_library import ReferenceLibrary


class FigureFamilyCoverageTests(unittest.TestCase):
    def test_taxonomy_covers_the_common_paper_figure_families(self):
        expected = {
            "comparison_effect", "distribution_uncertainty", "trend_trajectory",
            "paired_operating_point", "classification_diagnostics", "relationship_embedding",
            "matrix_array", "network_flow_set", "spatial_image", "mechanism_architecture",
            "statistical_discovery", "optimization_sensitivity",
        }
        self.assertTrue(expected.issubset(FIGURE_FAMILIES))
        for family_id, spec in FIGURE_FAMILIES.items():
            self.assertTrue(spec["figure_types"], family_id)
            self.assertTrue(spec["selection_rule"], family_id)
            self.assertTrue(spec["must_observe"], family_id)

    def test_audit_measures_reference_library_coverage_and_gaps(self):
        report = build_coverage_report(ReferenceLibrary())
        self.assertEqual(report["family_count"], len(FIGURE_FAMILIES))
        self.assertGreaterEqual(report["covered_family_count"], 6)
        self.assertTrue(report["missing_families"])
        self.assertTrue(all("candidate_ids" in item for item in report["families"] ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
