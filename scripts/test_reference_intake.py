from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference_library import ReferenceLibrary
from reference_image_analysis import analyze_image
from generate_adapters import _manifest_version, _runtime_files


class TestReferenceIntake(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="pfd_intake_"))
        (self.root / "SKILL.md").write_text("# test\n", encoding="utf-8")
        self.lib = ReferenceLibrary(root=self.root, registry_path=self.root / "registry.jsonl")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _image(self, name: str, accent: str = "#2166ac") -> Path:
        path = self.root / name
        image = Image.new("RGB", (420, 240), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((40, 40, 180, 190), fill=accent)
        draw.line((230, 190, 380, 50), fill="#b2182b", width=8)
        image.save(path)
        return path

    def test_ingest_writes_canonical_and_derivative_metadata(self):
        ref = self.lib.ingest(self._image("reference.png"), "grouped_bar")
        self.assertEqual(ref.metadata["dimensions"], [420, 240])
        self.assertEqual(ref.metadata["colorspace"], "sRGB_assumed")
        self.assertFalse(ref.metadata["has_alpha"])
        self.assertTrue(ref.metadata["perceptual_hash"])
        self.assertTrue(ref.image_path.exists())
        self.assertTrue(ref.preview_path and ref.preview_path.exists())
        self.assertTrue(ref.thumbnail_path and ref.thumbnail_path.exists())
        self.assertEqual(ref.metadata["original_quality"], "unassessed")
        self.assertFalse(ref.metadata["eligible_for_style"])
        ok, problems = self.lib.validate()
        self.assertTrue(ok, problems)

    def test_near_duplicate_is_recorded_as_alias(self):
        first = self.lib.ingest(self._image("first.png"), "grouped_bar")
        second = self.lib.ingest(self._image("second.png", "#2166ad"), "grouped_bar")
        self.assertEqual(second.id, first.id)
        self.assertEqual(len(second.metadata["aliases"]), 1)
        self.assertEqual(len(self.lib.all()), 1)

    def test_analyzer_emits_objective_facts(self):
        path = self._image("analysis.png")
        card = analyze_image(path, figure_type="grouped_bar")
        self.assertEqual(card["schema_version"], "2.0")
        self.assertEqual(card["canvas"]["colorspace"], "sRGB_assumed")
        self.assertIn("perceptual_hash", card)
        self.assertIn("geometry", card)
        self.assertIn("whitespace_map", card)
        self.assertEqual(card["panels"]["count"], 1)

    def test_adapter_uses_manifest_version_and_runtime_bundle(self):
        self.assertTrue(_manifest_version())
        self.assertIn("scripts/", _runtime_files())
        self.assertIn("schemas/", _runtime_files())
        self.assertIn("indexes/", _runtime_files())


if __name__ == "__main__":
    unittest.main()
