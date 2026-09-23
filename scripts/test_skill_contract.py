from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class SkillArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.manifest = yaml.safe_load((ROOT / "manifest.yaml").read_text(encoding="utf-8"))

    def test_entrypoint_is_a_thin_router(self):
        self.assertLessEqual(len(self.skill.splitlines()), 120)
        self.assertLessEqual(len(self.skill), 8000)
        self.assertTrue((ROOT / "manifest.yaml").is_file())

    def test_entrypoint_keeps_scientific_semantics_and_final_qa_mandatory(self):
        lowered = self.skill.lower()
        self.assertIn("scientific meaning", lowered)
        self.assertIn("final qa", lowered)
        self.assertIn("pfd run", lowered)

    def test_global_visual_language_remains_mandatory(self):
        lowered = self.skill.lower()
        for phrase in ("soft segmentation", "whitespace", "low-saturation", "legends"):
            self.assertIn(phrase, lowered)

    def test_reference_inspection_precedes_design_and_render(self):
        self.assertLess(self.skill.find("inspect the selected pixels"), self.skill.find("render"))
        self.assertIn("structure", self.skill)
        self.assertIn("style", self.skill)

    def test_manifest_defines_workflow_stages_without_reading_lists(self):
        self.assertNotIn("always_load", self.manifest)
        self.assertNotIn("routes", self.manifest)
        self.assertEqual(self.manifest["workflows"]["review"]["stages"], ["Route", "Intake", "QA"])
        self.assertEqual(self.manifest["conditions"]["qa_failed"]["insert_once"], ["Critique", "Repair", "Render", "QA"])

    def test_create_and_revise_add_reference_stages_conditionally(self):
        condition = self.manifest["conditions"]["reference_present"]
        self.assertEqual(condition["modes"], ["create", "revise"])
        self.assertEqual(condition["stages"], ["Reference Retrieval", "Reference Inspection", "Compare"])

    def test_evaluation_and_champion_scripts_are_not_mandatory_skill_context(self):
        lowered = self.skill.lower()
        for term in ("recall@1", "ndcg@3", "visual-baseline-v1", "challenger win rate", "champion board"):
            self.assertNotIn(term, lowered)
        self.assertIn("evaluation", self.manifest["operations"])

    def test_tex_reference_remains_routed_only_for_tex_work(self):
        self.assertIn("tex_backend", self.skill)
        self.assertIn("references/tex-rendering.md", self.skill)
        self.assertIn("rules/backend/tex.yaml", self.manifest["route_rulesets"]["tex_backend"])

    def test_reference_adaptation_contract_remains_available(self):
        source = (ROOT / "references" / "reference-driven-reconstruction.md").read_text(encoding="utf-8")
        for level in ("exact_reuse", "structural_adaptation", "style_only", "build_new"):
            self.assertIn(level, source)


class SelfCheckTests(unittest.TestCase):
    def test_self_check_accepts_repository(self):
        from scripts.check_skill_contract import validate_skill

        report = validate_skill(ROOT)
        self.assertTrue(report["ok"], report["errors"])

    def test_self_check_rejects_unknown_workflow_stage(self):
        from scripts.check_skill_contract import validate_skill

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text("---\nname: publication-figure-design\ndescription: short\n---\n", encoding="utf-8")
            (root / "manifest.yaml").write_text(yaml.safe_dump({"workflows": {"create": {"stages": ["Ghost"]}}}), encoding="utf-8")
            report = validate_skill(root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("unknown stage" in error for error in report["errors"]))

    def test_self_check_rejects_legacy_reading_list_contract(self):
        from scripts.check_skill_contract import validate_skill

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text("---\nname: publication-figure-design\ndescription: short\n---\n", encoding="utf-8")
            (root / "manifest.yaml").write_text("always_load: []\nroutes: {}\n", encoding="utf-8")
            report = validate_skill(root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("legacy reading-list" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
