from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference_image_analysis import analyze_image, compare_images


class TestReferenceImageAnalysis(unittest.TestCase):
    def _image(self, path: Path, *, accent: str = "#2166ac") -> None:
        image = Image.new("RGB", (240, 120), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((20, 20, 100, 90), fill=accent)
        draw.line((120, 90, 220, 25), fill="#b2182b", width=4)
        image.save(path)

    def test_analyze_image_emits_reproducible_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "reference.png"
            card_path = Path(tmp) / "figure_card.json"
            self._image(image_path)

            card = analyze_image(image_path, output=card_path, figure_type="grouped_bar")

            self.assertEqual(card["figure_type"], "grouped_bar")
            self.assertEqual(card["canvas"]["width_px"], 240)
            self.assertEqual(card["canvas"]["height_px"], 120)
            self.assertGreaterEqual(len(card["palette"]["dominant"]), 2)
            self.assertTrue(card["background"]["near_white"])
            self.assertTrue(card_path.exists())
            self.assertEqual(json.loads(card_path.read_text(encoding="utf-8")), card)

    def test_compare_images_reports_ssim_and_size_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.png"
            second = Path(tmp) / "second.png"
            self._image(first)
            self._image(second, accent="#2ca25f")

            report = compare_images(first, second)

            self.assertEqual(report["size"], [240, 120])
            self.assertIn("ssim", report)
            self.assertGreaterEqual(report["ssim"], 0.0)
            self.assertLess(report["ssim"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
