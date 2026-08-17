# -*- coding: utf-8 -*-
"""Contract tests for the evidence-first academic figure skill architecture."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_entrypoint_is_a_short_router(self):
        self.assertLessEqual(len(self.skill.splitlines()), 300)
        self.assertTrue((ROOT / "manifest.yaml").is_file())

    def test_frontmatter_advertises_paired_uncertainty_figures(self):
        description = self.skill.split("description:", 1)[1].split("\n---", 1)[0].lower()
        self.assertIn("paired operating-point", description)
        self.assertIn("uncertainty-aware", description)

    def test_reference_evidence_precedes_asset_selection(self):
        inspect_at = self.skill.find("Open every concrete reference")
        asset_at = self.skill.find("Select implementation material")
        self.assertGreaterEqual(inspect_at, 0)
        self.assertGreater(asset_at, inspect_at)

    def test_unified_adaptation_ladder_is_declared(self):
        for level in ("exact_reuse", "structural_adaptation", "style_only", "build_new"):
            self.assertIn(level, self.skill)
        for dimension in (
            "panel topology",
            "mark geometry",
            "layer topology",
            "data encoding",
            "annotation/legend model",
        ):
            self.assertIn(dimension, self.skill)

    def test_backend_policy_and_mixed_exception_are_routed(self):
        for phrase in ("explicit request", "workflow requirement", "saved preference", "final assembler"):
            self.assertIn(phrase, self.skill)
        self.assertIn("references/backend-selection.md", self.skill)
        self.assertTrue((ROOT / "scripts" / "backend_preference.py").is_file())

    def test_new_contract_resources_are_routed(self):
        expected = (
            "references/asset-adaptation.md",
            "references/figure-legend-contract.md",
            "references/privacy-provenance.md",
            "scripts/audit_pdf_text.py",
            "scripts/check_skill_contract.py",
        )
        for relative in expected:
            self.assertIn(relative, self.skill)
            self.assertTrue((ROOT / relative).is_file(), relative)
        self.assertTrue((ROOT / "agents" / "openai.yaml").is_file())

    def test_source_reconstruction_route_is_audited_not_imported(self):
        routed = self.skill.lower() + (ROOT / "manifest.yaml").read_text(encoding="utf-8").lower()
        self.assertIn("source-reconstruction-library.md", routed)
        self.assertIn("check_source_reconstruction_library.py", routed)
        self.assertNotIn("import figures4papers", routed)
        self.assertNotIn("copy figures4papers", routed)
        self.assertNotIn("assets/figures4papers", routed)

    def test_exact_source_catalog_checker_is_required_for_skill_maintenance(self):
        manifest = (ROOT / "manifest.yaml").read_text(encoding="utf-8")
        maintain = manifest.split("  maintain_skill:", 1)[1].split("  source_reconstruction:", 1)[0]
        source = manifest.split("  source_reconstruction:", 1)[1].split("\n\nbackend_policy:", 1)[0]
        self.assertIn("scripts/check_source_reference_catalog.py", maintain)
        self.assertIn("scripts/check_source_reference_catalog.py", source)
        self.assertIn("source_reference_catalog: \"python scripts/check_source_reference_catalog.py\"", manifest)
        self.assertIn("scripts/check_source_reference_catalog.py", self.skill)

    def test_palette_and_rendered_contrast_gates_are_routed(self):
        manifest = (ROOT / "manifest.yaml").read_text(encoding="utf-8")
        self.assertIn("references/color-palettes.md", self.skill)
        self.assertIn("scripts/rendered_contrast.py", self.skill)
        self.assertIn("scripts/rendered_contrast.py", manifest)
        self.assertIn("scripts/palette_manager.py", manifest)

    def test_visual_optimization_has_a_low_freedom_task_packet_entrypoint(self):
        manifest = (ROOT / "manifest.yaml").read_text(encoding="utf-8")
        script = ROOT / "scripts" / "prepare_visual_optimization.py"
        self.assertTrue(script.is_file())
        self.assertIn("prepare_visual_optimization.py", self.skill)
        self.assertIn("prepare_visual_optimization.py", manifest)
        self.assertIn("Do not edit plotting source", self.skill)

    def test_art_direction_catalog_is_routed_for_conceptual_and_multi_panel_figures(self):
        catalog = ROOT / "references" / "art-direction.md"
        self.assertTrue(catalog.is_file())
        self.assertIn("references/art-direction.md", self.skill)
        text = catalog.read_text(encoding="utf-8")
        for direction in (
            "hero_illustration",
            "editorial_evidence_chain",
            "modular_blueprint",
            "specimen_evidence_atlas",
            "analytic_minimalism",
            "comparative_storyboard",
        ):
            self.assertIn(direction, text)

    def test_encoding_and_uncertainty_decision_rules_are_routed(self):
        manifest = (ROOT / "manifest.yaml").read_text(encoding="utf-8")
        resource = "references/encoding-and-uncertainty.md"
        self.assertIn(resource, self.skill)
        self.assertIn(resource, manifest)
        self.assertTrue((ROOT / resource).is_file())
        guidance = (ROOT / resource).read_text(encoding="utf-8")
        for phrase in (
            "paired comparison",
            "continuous relationship",
            "primary visual channel",
            "uncertainty",
            "operating-point",
            "thumbnail",
        ):
            self.assertIn(phrase, guidance)


class SelfCheckTests(unittest.TestCase):
    def test_self_check_accepts_repository(self):
        from check_skill_contract import validate_skill

        report = validate_skill(ROOT)
        self.assertTrue(report["ok"], report["errors"])

    def test_self_check_rejects_missing_route_target(self):
        from check_skill_contract import validate_skill

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text(
                "---\nname: publication-figure-design\ndescription: test\n---\n"
                "Open every concrete reference.\nSelect implementation material.\n"
                "`references/missing.md`\n",
                encoding="utf-8",
            )
            (root / "manifest.yaml").write_text("name: publication-figure-design\n", encoding="utf-8")
            report = validate_skill(root)
        self.assertFalse(report["ok"])
        self.assertIn("missing", " ".join(report["errors"]).lower())

    def test_self_check_validates_manifest_route_targets(self):
        from check_skill_contract import validate_skill

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "agents").mkdir()
            (root / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
            (root / "SKILL.md").write_text(
                "---\nname: publication-figure-design\ndescription: test\n---\n"
                "Open every concrete reference.\nSelect implementation material.\n"
                + "\n".join(("exact_reuse", "structural_adaptation", "style_only", "build_new"))
                + "\npanel topology\nmark geometry\nlayer topology\ndata encoding\n"
                "annotation/legend model\nfinal assembler\n",
                encoding="utf-8",
            )
            (root / "manifest.yaml").write_text(
                "name: publication-figure-design\nalways_load:\n  - \"references/missing.md\"\n"
                "routes: {}\nbackend_policy: {}\nvalidation: {}\n",
                encoding="utf-8",
            )
            report = validate_skill(root)
        self.assertFalse(report["ok"])
        self.assertIn("references/missing.md", " ".join(report["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
