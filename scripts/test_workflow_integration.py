# -*- coding: utf-8 -*-
"""Integration tests for Phase 2 workflow changes.

These tests verify that SKILL.md contains the expected workflow hooks and that
ReferenceLibrary supports the queries described in the workflow.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference_library import ReferenceLibrary, _resolve_skill_root


class TestSkillMdWorkflowHooks(unittest.TestCase):
    """Verify that SKILL.md contains the Phase 2 integration instructions."""

    @classmethod
    def setUpClass(cls):
        root = _resolve_skill_root()
        cls.skill_md = (root / "SKILL.md").read_text(encoding="utf-8")

    def test_task_dispatch_section_exists(self):
        self.assertIn("## Task Dispatch", self.skill_md)

    def test_five_modes_defined(self):
        for mode in ("create", "revise", "review", "export", "reference"):
            self.assertIn(f"**{mode}**", self.skill_md)

    def test_reference_mode_shortcuts(self):
        self.assertIn("ReferenceLibrary().ingest", self.skill_md)
        self.assertIn("archive_generated_figure", self.skill_md)
        self.assertIn("query(figure_type=\"GroupedViolin\"", self.skill_md)

    def test_revise_export_do_not_use_full_pipeline(self):
        self.assertIn("Jump to affected steps only", self.skill_md)
        self.assertIn("Load existing figure/code, change export parameters", self.skill_md)

    def test_step_4_5_section_exists(self):
        self.assertIn("### Step 4.5: Visual Reference Retrieval", self.skill_md)

    def test_default_reference_limit_is_three(self):
        self.assertIn("limit=3", self.skill_md)
        self.assertIn("Default limit:** 3 references", self.skill_md)

    def test_production_semantics_priority_over_visual_style(self):
        # The instruction must state that scientific semantics cannot be overridden
        # by a visual reference.
        self.assertIn("Do NOT override scientific semantics or data structure", self.skill_md)
        self.assertIn("Use it only for visual language", self.skill_md)

    def test_palette_priority_order(self):
        text = self.skill_md
        # User explicit colors > user explicit palette > visual reference > default
        idx_user_colors = text.find("User explicit colors")
        idx_user_palette = text.find("User explicit palette")
        idx_ref = text.find("Visual reference original palette")
        idx_default = text.find("Skill default palette")
        self.assertGreater(idx_user_colors, 0)
        self.assertGreater(idx_user_palette, idx_user_colors)
        self.assertGreater(idx_ref, idx_user_palette)
        self.assertGreater(idx_default, idx_ref)

    def test_palette_policy_preserve_and_adaptable_mentioned(self):
        self.assertIn("palette_policy", self.skill_md)
        self.assertIn("preserve", self.skill_md)
        self.assertIn("adaptable", self.skill_md)

    def test_visual_source_report_in_delivery(self):
        self.assertIn("Visual Source Report", self.skill_md)
        self.assertIn("Production asset:", self.skill_md)
        self.assertIn("Visual reference:", self.skill_md)

    def test_visual_reference_library_in_references_table(self):
        self.assertIn("references/visual-reference-library.md", self.skill_md)


class TestWorkflowReferenceQueries(unittest.TestCase):
    """Verify ReferenceLibrary supports the workflow queries."""

    def setUp(self):
        self.skill_root = Path(tempfile.mkdtemp(prefix="afs_workflow_test_"))
        (self.skill_root / "SKILL.md").write_text("# skill\n", encoding="utf-8")
        self.lib = ReferenceLibrary(root=self.skill_root)

    def tearDown(self):
        shutil.rmtree(self.skill_root, ignore_errors=True)

    def _make_image(self, name: str, data: bytes) -> Path:
        p = self.skill_root / name
        p.write_bytes(data)
        return p

    def test_create_workflow_can_query_reference(self):
        src = self._make_image("ref1.png", b"\x89PNG\r\n\x1a\nREF001")
        self.lib.ingest(
            src,
            "GroupedViolin",
            metadata_override={
                "tags": ["pastel", "minimal"],
                "journal_style": "Nature",
                "palette": "summer_beach",
                "aesthetic_rating": 4,
            },
        )

        refs = self.lib.query(
            figure_type="GroupedViolin",
            tags=["pastel"],
            journal_style="Nature",
            min_aesthetic_rating=3,
            limit=3,
        )
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].figure_type, "GroupedViolin")

    def test_query_returns_at_most_limit_candidates(self):
        for i in range(5):
            src = self._make_image(f"ref{i}.png", f"\x89PNG\r\n\x1a\nREF{i:03d}".encode())
            self.lib.ingest(
                src,
                "PCA",
                metadata_override={
                    "tags": ["pastel"],
                    "aesthetic_rating": 4,
                },
            )

        refs = self.lib.query(figure_type="PCA", tags=["pastel"], limit=3)
        self.assertLessEqual(len(refs), 3)

    def test_no_reference_falls_back_gracefully(self):
        refs = self.lib.query(figure_type="GroupedViolin", tags=["pastel"], limit=3)
        self.assertEqual(len(refs), 0)

    def test_reference_task_can_archive_generated_figure(self):
        img = self._make_image("gen.png", b"\x89PNG\r\n\x1a\nGEN001")
        code = self.skill_root / "gen.py"
        code.write_text("# code\n", encoding="utf-8")

        ref = self.lib.archive_generated_figure(
            image_path=img,
            figure_type="StackedBarScatter",
            code_path=code,
            metadata_override={"palette": "fresh_holiday", "aesthetic_rating": 5},
        )
        self.assertEqual(ref.scope, "generated-archive")
        self.assertEqual(ref.metadata["palette"], "fresh_holiday")
        self.assertTrue(ref.code_path.exists())

    def test_palette_policy_preserve_default(self):
        src = self._make_image("policy.png", b"\x89PNG\r\n\x1a\nPOLICY")
        ref = self.lib.ingest(
            src,
            "Violin",
            metadata_override={"palette": "sweet_macaron"},
        )
        self.assertEqual(ref.metadata["palette_policy"], "preserve")

    def test_palette_policy_adaptable_can_be_set(self):
        src = self._make_image("adapt.png", b"\x89PNG\r\n\x1a\nADAPT")
        ref = self.lib.ingest(
            src,
            "Violin",
            metadata_override={"palette": "sweet_macaron", "palette_policy": "adaptable"},
        )
        self.assertEqual(ref.metadata["palette_policy"], "adaptable")

    def test_figure_type_query_only_matches_same_type(self):
        violin = self._make_image("v.png", b"\x89PNG\r\n\x1a\nVIOLIN")
        pca = self._make_image("p.png", b"\x89PNG\r\n\x1a\nPCA001")
        self.lib.ingest(violin, "Violin", metadata_override={"tags": ["pastel"]})
        self.lib.ingest(pca, "PCA", metadata_override={"tags": ["pastel"]})

        refs = self.lib.query(figure_type="Violin", tags=["pastel"])
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].figure_type, "Violin")

    def test_n_groups_filter_works(self):
        src = self._make_image("ng.png", b"\x89PNG\r\n\x1a\nNGROUP")
        self.lib.ingest(
            src,
            "GroupedViolin",
            metadata_override={"tags": ["minimal"], "n_groups": 4},
        )

        refs = self.lib.query(figure_type="GroupedViolin", n_groups=4)
        self.assertEqual(len(refs), 1)

        refs = self.lib.query(figure_type="GroupedViolin", n_groups=3)
        self.assertEqual(len(refs), 0)

    def test_resolve_visual_style_user_colors_win(self):
        src = self._make_image("ref_colors.png", b"\x89PNG\r\n\x1a\nREFCLR")
        ref = self.lib.ingest(
            src,
            "GroupedViolin",
            metadata_override={"palette": "summer_beach", "palette_policy": "preserve"},
        )
        style = self.lib.resolve_visual_style(
            "GroupedViolin",
            reference_id=ref.id,
            user_colors=["#111111", "#222222", "#333333"],
            n=3,
        )
        self.assertEqual(style["source"], "user_colors")
        self.assertEqual(style["colors"], ["#111111", "#222222", "#333333"])

    def test_resolve_visual_style_user_palette_wins_over_reference(self):
        src = self._make_image("ref_palette.png", b"\x89PNG\r\n\x1a\nREFPAL")
        ref = self.lib.ingest(
            src,
            "GroupedViolin",
            metadata_override={"palette": "summer_beach", "palette_policy": "preserve"},
        )
        style = self.lib.resolve_visual_style(
            "GroupedViolin",
            reference_id=ref.id,
            user_palette="sweet_macaron",
            n=3,
        )
        self.assertEqual(style["source"], "user_palette")
        self.assertEqual(style["palette"], "sweet_macaron")
        self.assertEqual(len(style["colors"]), 3)
        # sweet_macaron first three colors
        self.assertEqual(style["colors"][0], "#F7A6AC")

    def test_resolve_visual_style_preserve_uses_reference_palette(self):
        src = self._make_image("preserve_ref.png", b"\x89PNG\r\n\x1a\nPRESERVE")
        ref = self.lib.ingest(
            src,
            "GroupedViolin",
            metadata_override={"palette": "summer_beach", "palette_policy": "preserve"},
        )
        style = self.lib.resolve_visual_style("GroupedViolin", reference_id=ref.id, n=3)
        self.assertEqual(style["source"], "reference")
        self.assertEqual(style["palette_policy"], "preserve")
        self.assertEqual(style["colors"], ["#FC757B", "#F97F5F", "#FAA26F"])

    def test_resolve_visual_style_adaptable_uses_reference_palette(self):
        src = self._make_image("adaptable_ref.png", b"\x89PNG\r\n\x1a\nADAPTABLE")
        ref = self.lib.ingest(
            src,
            "GroupedViolin",
            metadata_override={"palette": "summer_beach", "palette_policy": "adaptable"},
        )
        style = self.lib.resolve_visual_style("GroupedViolin", reference_id=ref.id, n=3)
        self.assertEqual(style["source"], "reference")
        self.assertEqual(style["palette_policy"], "adaptable")
        self.assertEqual(style["colors"], ["#FC757B", "#F97F5F", "#FAA26F"])

    def test_resolve_visual_style_no_reference_falls_back_to_default(self):
        style = self.lib.resolve_visual_style("GroupedViolin", n=3)
        self.assertEqual(style["source"], "default")
        self.assertEqual(len(style["colors"]), 3)

    def test_resolve_visual_style_deterministic(self):
        src = self._make_image("det.png", b"\x89PNG\r\n\x1a\nDET")
        ref = self.lib.ingest(
            src,
            "GroupedViolin",
            metadata_override={"palette": "summer_beach", "palette_policy": "preserve"},
        )
        s1 = self.lib.resolve_visual_style("GroupedViolin", reference_id=ref.id, n=3)
        s2 = self.lib.resolve_visual_style("GroupedViolin", reference_id=ref.id, n=3)
        self.assertEqual(s1["colors"], s2["colors"])


class TestComposePaletteIntegration(unittest.TestCase):
    """Verify compose.py can safely consume palette_manager palettes."""

    def test_compose_get_palette_uses_journal_default_without_palette_arg(self):
        from compose import get_palette
        colors = get_palette(3, role="categorical")
        self.assertEqual(colors, ["#2166AC", "#B2182B", "#1B7837"])

    def test_compose_get_palette_can_use_palette_manager(self):
        from compose import get_palette
        colors = get_palette(3, role="categorical", palette="summer_beach")
        self.assertEqual(colors, ["#FC757B", "#F97F5F", "#FAA26F"])

    def test_compose_sequential_unaffected_by_palette_arg(self):
        from compose import get_palette, SEQUENTIAL
        colors = get_palette(3, role="sequential", palette="summer_beach")
        self.assertEqual(colors, SEQUENTIAL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
