# -*- coding: utf-8 -*-
"""Unit tests for scripts/production_asset_manager.py."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Allow standalone execution during development.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from production_asset_manager import (
    PRODUCTION_METADATA_FIELDS,
    ProductionAsset,
    ProductionAssetLibrary,
    validate_metadata,
)


class TestMetadataValidation(unittest.TestCase):
    def test_valid_template_metadata(self):
        meta = {
            "id": "groupedviolin_default",
            "figure_type": "GroupedViolin",
            "asset_kind": "template",
            "runtime": "python",
            "production_ready": True,
        }
        ok, errors = validate_metadata(meta)
        self.assertTrue(ok, errors)

    def test_missing_required_fields(self):
        ok, errors = validate_metadata({})
        self.assertFalse(ok)
        self.assertIn("Missing required field: id", errors)
        self.assertIn("Missing required field: figure_type", errors)
        self.assertIn("Missing required field: asset_kind", errors)
        self.assertIn("Missing required field: runtime", errors)
        self.assertIn("Missing required field: production_ready", errors)

    def test_invalid_asset_kind(self):
        ok, errors = validate_metadata({
            "id": "x", "figure_type": "X", "asset_kind": "unknown",
            "runtime": "python", "production_ready": False,
        })
        self.assertFalse(ok)
        self.assertTrue(any("asset_kind" in e for e in errors))

    def test_invalid_runtime(self):
        ok, errors = validate_metadata({
            "id": "x", "figure_type": "X", "asset_kind": "template",
            "runtime": "julia", "production_ready": True,
        })
        self.assertFalse(ok)
        self.assertTrue(any("runtime" in e for e in errors))

    def test_invalid_palette_policy(self):
        ok, errors = validate_metadata({
            "id": "x", "figure_type": "X", "asset_kind": "template",
            "runtime": "python", "production_ready": True,
            "palette_policy": "flexible",
        })
        self.assertFalse(ok)
        self.assertTrue(any("palette_policy" in e for e in errors))

    def test_coerces_string_production_ready(self):
        ok, errors = validate_metadata({
            "id": "x", "figure_type": "X", "asset_kind": "template",
            "runtime": "python", "production_ready": "true",
        })
        self.assertTrue(ok, errors)


class TestProductionAsset(unittest.TestCase):
    def test_properties(self):
        meta = {
            "id": "foo_default",
            "figure_type": "Foo",
            "asset_kind": "template",
            "runtime": "python",
            "production_ready": True,
            "preview": "foo.png",
        }
        asset = ProductionAsset(meta)
        self.assertEqual(asset.id, "foo_default")
        self.assertEqual(asset.figure_type, "Foo")
        self.assertEqual(asset.asset_kind, "template")
        self.assertTrue(asset.production_ready)
        self.assertIsNotNone(asset.preview)


class TestProductionAssetLibraryOnRealRepo(unittest.TestCase):
    def setUp(self):
        self.lib = ProductionAssetLibrary()

    def test_scan_finds_pilot_assets(self):
        assets = self.lib.scan(force=True)
        ids = {a.id for a in assets}
        expected = {
            "groupedviolin_default",
            "stackedbarscatter_default",
            "marginaldensity_default",
            "pca_default",
            "heatmap_default",
        }
        self.assertTrue(expected.issubset(ids), f"Missing pilots; found {ids}")

    def test_get_by_id(self):
        asset = self.lib.get("groupedviolin_default")
        self.assertIsNotNone(asset)
        self.assertEqual(asset.asset_kind, "template")
        self.assertTrue(asset.production_ready)

    def test_get_by_path(self):
        asset = self.lib.get_by_path("PCA", "default")
        self.assertIsNotNone(asset)
        self.assertEqual(asset.runtime, "r")

    def test_list_filters_by_kind(self):
        templates = self.lib.list(asset_kind="template")
        template_ids = {a.id for a in templates}
        self.assertIn("groupedviolin_default", template_ids)
        self.assertIn("marginaldensity_default", template_ids)
        examples = self.lib.list(asset_kind="example")
        example_ids = {a.id for a in examples}
        self.assertIn("stackedbarscatter_default", example_ids)
        self.assertIn("pca_default", example_ids)

    def test_query_defaults_to_production_ready(self):
        results = self.lib.query("heatmap")
        self.assertTrue(all(a.production_ready for a in results))

    def test_query_limits_results(self):
        results = self.lib.query("GroupedViolin", limit=1)
        self.assertEqual(len(results), 1)

    def test_query_sorts_template_first(self):
        results = self.lib.query(figure_type=None)  # type: ignore[arg-type]
        kinds = [a.asset_kind for a in results]
        if len(kinds) >= 2:
            # Templates should appear before examples when production_ready matches.
            self.assertLessEqual(
                {"template": 0, "reusable": 1, "example": 2}.get(kinds[0], 99),
                {"template": 0, "reusable": 1, "example": 2}.get(kinds[-1], 99),
            )

    def test_validate_pilots_pass(self):
        ok, problems = self.lib.validate()
        self.assertTrue(ok, problems)


class TestPromotion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "SKILL.md").write_text("skill", encoding="utf-8")
        (self.root / "assets" / "visual-references" / "generated-archive").mkdir(parents=True)
        (self.root / "assets" / "figures").mkdir(parents=True)

        # Create a reviewed, production-ready visual reference.
        ref_dir = self.root / "assets" / "visual-references" / "generated-archive" / "abc123"
        ref_dir.mkdir(parents=True)
        (ref_dir / "image.png").write_bytes(b"pngdata")
        (ref_dir / "code.py").write_text("print('hello')", encoding="utf-8")
        meta = {
            "id": "abc123",
            "scope": "generated-archive",
            "figure_type": "GroupedViolin",
            "image_path": "assets/visual-references/generated-archive/abc123/image.png",
            "code_path": "assets/visual-references/generated-archive/abc123/code.py",
            "review_status": "reviewed",
            "production_ready": True,
            "palette_policy": "preserve",
            "created_at": "2024-01-01T00:00:00Z",
        }
        (ref_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")

        self.lib = ProductionAssetLibrary(root=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_promote_from_visual_reference(self):
        asset = self.lib.promote_from_visual_reference("abc123", notes="Promoted for testing.")
        self.assertEqual(asset.figure_type, "GroupedViolin")
        self.assertEqual(asset.asset_kind, "template")
        self.assertTrue(asset.production_ready)
        self.assertEqual(asset.metadata["notes"], "Promoted for testing.")

        target_dir = self.root / "assets" / "figures" / "GroupedViolin"
        self.assertTrue((target_dir / "metadata.json").exists())
        self.assertTrue((target_dir / "image.png").exists())
        self.assertTrue((target_dir / "code.py").exists())

    def test_promote_rejects_pending_reference(self):
        ref_dir = self.root / "assets" / "visual-references" / "generated-archive" / "abc123"
        meta = json.loads((ref_dir / "metadata.json").read_text(encoding="utf-8"))
        meta["review_status"] = "pending"
        (ref_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")

        with self.assertRaises(ValueError) as cm:
            self.lib.promote_from_visual_reference("abc123")
        self.assertIn("review_status", str(cm.exception))

    def test_promote_rejects_not_production_ready(self):
        ref_dir = self.root / "assets" / "visual-references" / "generated-archive" / "abc123"
        meta = json.loads((ref_dir / "metadata.json").read_text(encoding="utf-8"))
        meta["production_ready"] = False
        (ref_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")

        with self.assertRaises(ValueError) as cm:
            self.lib.promote_from_visual_reference("abc123")
        self.assertIn("production_ready", str(cm.exception))


class TestPackageImport(unittest.TestCase):
    def test_scripts_init_exports_symbols(self):
        # When this file is run directly, Python may resolve `scripts` as the
        # current module. Run this assertion only in package context.
        if "__main__" in sys.modules and sys.modules["__main__"].__file__ and sys.modules["__main__"].__file__.endswith("test_production_asset_manager.py"):
            self.skipTest("scripts package import can only be verified when run as module")
        from scripts import (
            PRODUCTION_METADATA_FIELDS,
            ProductionAsset,
            ProductionAssetLibrary,
        )
        self.assertIn("id", PRODUCTION_METADATA_FIELDS)
        self.assertTrue(callable(ProductionAssetLibrary))


if __name__ == "__main__":
    unittest.main()
