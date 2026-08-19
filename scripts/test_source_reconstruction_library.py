# -*- coding: utf-8 -*-
"""Tests for the source-by-source visual grammar reconstruction library."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


class SourceReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="afs_reconstruction_"))
        self.nature = self.tmp / "nature-figure"
        self.figures = self.tmp / "figures4papers"
        self.skill = self.tmp / "skill"
        (self.skill / "scripts").mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("# test skill\n", encoding="utf-8")
        for name in ("__init__.py", "source_reconstruction_library.py", "reference_library.py", "palette_manager.py", "palettes.py"):
            shutil.copy2(SCRIPT_DIR / name, self.skill / "scripts" / name)

        self._image(self.nature / "assets/chart-atlas/atlas-01-bar-charts.png", (120, 80), "#d9e9f5")
        self._image(self.nature / "assets/gallery/fig2-spatial-imaging-rich.png", (90, 120), "#f2ddd3")
        self._image(
            self.nature / "assets/figures4papers/ignored.png", (60, 60), "#111111"
        )
        self._image(self.figures / "figure_VIGIL/figures/comparison_radar.png", (100, 100), "#dde7d5")
        self._image(self.figures / "figure_RNAGenScape/figures/manifold.png", (140, 90), "#e8dfef")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def _image(path: Path, size: tuple[int, int], color: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", size, color).save(path)

    def test_discovers_selected_sources_with_relative_provenance(self):
        from source_reconstruction_library import discover_sources

        records = discover_sources(self.nature, self.figures)

        self.assertEqual(len(records), 4)
        self.assertEqual({r.repository for r in records}, {"nature-figure", "figures4papers"})
        self.assertFalse(any(Path(r.relative_path).is_absolute() for r in records))
        self.assertFalse(any("assets/figures4papers" in r.relative_path for r in records))
        self.assertEqual(len({r.source_sha256 for r in records}), 4)
        self.assertTrue(all(r.width > 0 and r.height > 0 for r in records))

        licensed = [r for r in records if r.repository == "nature-figure"]
        observed = [r for r in records if r.repository == "figures4papers"]
        self.assertTrue(all(r.license_class == "Apache-2.0" for r in licensed))
        self.assertTrue(all(r.source_action == "licensed_visual_source" for r in licensed))
        self.assertTrue(all(r.license_class == "unknown" for r in observed))
        self.assertTrue(all(r.source_action == "independent_reconstruction" for r in observed))

    def test_discovery_does_not_emit_pillow_large_image_warning(self):
        from source_reconstruction_library import discover_sources

        original_limit = Image.MAX_IMAGE_PIXELS
        Image.MAX_IMAGE_PIXELS = 100
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                discover_sources(self.nature, self.figures)
        finally:
            Image.MAX_IMAGE_PIXELS = original_limit
        self.assertFalse(any(issubclass(item.category, Image.DecompressionBombWarning) for item in caught))

    def test_classifies_observable_visual_families(self):
        from source_reconstruction_library import discover_sources, reconstruction_blueprint, visual_profile

        by_name = {Path(r.relative_path).name: r.visual_family for r in discover_sources(self.nature, self.figures)}
        self.assertEqual(by_name["atlas-01-bar-charts.png"], "grouped_bar")
        self.assertEqual(by_name["fig2-spatial-imaging-rich.png"], "spatial_image_plate")
        self.assertEqual(by_name["comparison_radar.png"], "radar_grid")
        self.assertEqual(by_name["manifold.png"], "manifold_3d")
        records = {Path(r.relative_path).name: r for r in discover_sources(self.nature, self.figures)}
        self.assertEqual(visual_profile(records["atlas-01-bar-charts.png"])["panel_grid"], [4, 4])
        self.assertGreaterEqual(visual_profile(records["fig2-spatial-imaging-rich.png"])["panel_count"], 6)

        bar = reconstruction_blueprint(records["atlas-01-bar-charts.png"])
        radar = reconstruction_blueprint(records["comparison_radar.png"])
        manifold = reconstruction_blueprint(records["manifold.png"])
        self.assertEqual(bar["blueprint_id"], "atlas_bar_charts")
        self.assertEqual(radar["blueprint_id"], "vigil_radar_comparison")
        self.assertEqual(manifold["blueprint_id"], "rnagenscape_manifold")
        self.assertNotEqual(bar["panel_recipes"], radar["panel_recipes"])
        self.assertTrue(all("kind" in panel for panel in bar["panel_recipes"]))

    def test_render_is_deterministic_valid_and_not_source_pixels(self):
        from source_reconstruction_library import discover_sources, render_reconstruction

        record = discover_sources(self.nature, self.figures)[0]
        out_a = self.tmp / "a.png"
        out_b = self.tmp / "b.png"
        render_reconstruction(record, out_a)
        render_reconstruction(record, out_b)

        self.assertEqual(out_a.read_bytes(), out_b.read_bytes())
        self.assertNotEqual(
            hashlib.sha256(out_a.read_bytes()).hexdigest(), record.source_sha256
        )
        with Image.open(out_a) as image:
            image.verify()

    def test_build_archives_one_record_per_source_and_is_idempotent(self):
        from source_reconstruction_library import build_reconstruction_library

        first = build_reconstruction_library(self.nature, self.figures, self.skill)
        second = build_reconstruction_library(self.nature, self.figures, self.skill)

        self.assertEqual(first["summary"]["source_count"], 4)
        self.assertEqual(second["summary"]["created_count"], 0)
        self.assertEqual(len(first["records"]), 4)
        self.assertEqual(len({r["source_fingerprint"] for r in first["records"]}), 4)
        self.assertEqual(len({r["archive_id"] for r in first["records"]}), 4)

        for item in first["records"]:
            self.assertEqual(item["scope"], "generated-archive")
            self.assertEqual(item["reconstruction_method"], "independent")
            self.assertFalse(Path(item["image_path"]).is_absolute())
            self.assertNotEqual(item["source_fingerprint"], item["output_sha256"])
            meta_path = self.skill / "assets/visual-references/generated-archive" / item["archive_id"] / "metadata.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(meta["source_fingerprint"], item["source_fingerprint"])
            self.assertEqual(meta["visual_family"], item["visual_family"])
            self.assertIn("observable_visual_grammar", meta)
            self.assertIn("reconstruction_blueprint", meta)
            self.assertTrue(meta["reconstruction_blueprint"]["blueprint_id"])
            self.assertEqual(meta["review_status"], "pending")
            self.assertIsNone(meta["aesthetic_rating"])
            self.assertFalse(meta["production_ready"])
            self.assertEqual(item["renderer_version"], 3)
            code = (self.skill / meta["code_path"]).read_text(encoding="utf-8")
            self.assertNotIn("figures4papers", code.lower())
            self.assertNotIn("nature-skills", code.lower())
            completed = subprocess.run(
                [sys.executable, str(self.skill / meta["code_path"])],
                cwd=self.tmp,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            (self.skill / meta["code_path"]).with_name("reproduced.png").unlink()

        manifest_path = self.skill / "assets/visual-references/source-reconstruction-manifest.json"
        stale = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in stale["records"]:
            item["renderer_version"] = 1
        manifest_path.write_text(json.dumps(stale), encoding="utf-8")
        migrated = build_reconstruction_library(self.nature, self.figures, self.skill)
        self.assertEqual(len(migrated["records"]), 4)
        self.assertTrue(all(item["renderer_version"] == 3 for item in migrated["records"]))

    def test_installed_checker_accepts_built_library(self):
        from source_reconstruction_library import (
            build_reconstruction_library,
            validate_installed_library,
        )

        build_reconstruction_library(self.nature, self.figures, self.skill)
        report = validate_installed_library(self.skill, expected_counts=None)
        self.assertTrue(report["ok"], report["errors"])

    def test_quarantine_resets_automated_aesthetic_approval(self):
        from source_reconstruction_library import (
            build_reconstruction_library,
            quarantine_installed_reconstructions,
        )

        manifest = build_reconstruction_library(self.nature, self.figures, self.skill)
        archive_id = manifest["records"][0]["archive_id"]
        meta_path = self.skill / "assets/visual-references/generated-archive" / archive_id / "metadata.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update({"review_status": "reviewed", "aesthetic_rating": 4, "production_ready": True})
        meta_path.write_text(json.dumps(meta), encoding="utf-8")

        report = quarantine_installed_reconstructions(self.skill)
        migrated = json.loads(meta_path.read_text(encoding="utf-8"))
        self.assertEqual(report["changed_count"], 1)
        self.assertEqual(migrated["review_status"], "pending")
        self.assertIsNone(migrated["aesthetic_rating"])
        self.assertFalse(migrated["production_ready"])

    def test_checker_rejects_a_manifest_without_source_specific_blueprint(self):
        from source_reconstruction_library import build_reconstruction_library, validate_installed_library

        build_reconstruction_library(self.nature, self.figures, self.skill)
        manifest_path = self.skill / "assets/visual-references/source-reconstruction-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["records"][0].pop("reconstruction_blueprint")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        report = validate_installed_library(self.skill, expected_counts=None)
        self.assertFalse(report["ok"])
        self.assertTrue(any("source-specific reconstruction blueprint" in error for error in report["errors"]))

    def test_exact_source_catalog_keeps_source_assets_separate_from_reconstructions(self):
        from source_reference_catalog import catalog_source_images
        from reference_library import ReferenceLibrary

        result = catalog_source_images(self.nature, self.figures, self.skill)
        self.assertEqual(result["cataloged_count"], 4)
        self.assertEqual(result["created_count"], 4)
        for item in result["records"]:
            metadata = json.loads(
                (self.skill / "assets/visual-references/references" / item["reference_id"] / "metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(metadata["reference_kind"], "exact_visual_source")
            self.assertEqual(metadata["review_status"], "pending")
            self.assertIn("reconstruction_blueprint", metadata)
        library = ReferenceLibrary(root=self.skill, registry_path=self.skill / "assets/registry.jsonl")
        self.assertEqual(library.query(figure_type="grouped_bar"), [])

    def test_exact_source_audit_makes_only_reviewed_originals_retrievable(self):
        from source_reference_catalog import catalog_source_images
        from audit_source_catalog_batch import audit_catalog
        from reference_library import ReferenceLibrary

        catalog_source_images(self.nature, self.figures, self.skill)
        catalog = json.loads(
            (self.skill / "assets/visual-references/source-reference-catalog.json").read_text(encoding="utf-8")
        )
        audit_file = self.skill / "source-audit.json"
        audit_file.write_text(
            json.dumps({"decisions": {
                record["blueprint_id"]: {"rating": 4.0, "notes": "Pixel-inspected test fixture."}
                for record in catalog["records"]
            }}),
            encoding="utf-8",
        )
        audit_catalog(self.skill, reviewer="test visual audit", audit_path=audit_file)
        library = ReferenceLibrary(root=self.skill, registry_path=self.skill / "assets/registry.jsonl")
        self.assertTrue(library.query(figure_type="grouped_bar"))
        source = library.get(result_id := json.loads(
            (self.skill / "assets/visual-references/source-reference-catalog.json").read_text(encoding="utf-8")
        )["records"][0]["reference_id"])
        self.assertEqual(source.metadata["review_status"], "reviewed")
        self.assertEqual(source.metadata["visual_review"]["reviewer"], "test visual audit")

    def test_source_catalog_checker_rejects_missing_manual_decision(self):
        from source_reference_catalog import catalog_source_images
        from check_source_reference_catalog import validate_source_catalog

        catalog_source_images(self.nature, self.figures, self.skill)
        audit = self.skill / "assets/visual-references/source-reference-visual-audit.json"
        audit.write_text(json.dumps({"decisions": {}}), encoding="utf-8")
        report = validate_source_catalog(self.skill, expected_count=None)
        self.assertFalse(report["ok"])
        self.assertTrue(any("manual decisions" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
