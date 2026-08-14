# -*- coding: utf-8 -*-
"""Tests for rendered text/background contrast evidence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from scripts.rendered_contrast import inspect_text_contrast


class RenderedContrastTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.image = Path(self.tmp.name) / "contrast.png"

    def tearDown(self):
        self.tmp.cleanup()

    def _save(self, background: str, text: str):
        image = Image.new("RGB", (300, 160), background)
        ImageDraw.Draw(image).text((80, 55), "0.039", fill=text)
        image.save(self.image)

    def test_white_text_on_light_cell_fails(self):
        self._save("#8DBAD5", "#FFFFFF")
        report = inspect_text_contrast(self.image, [(70, 45, 170, 90)])
        self.assertFalse(report["ready"], report)
        self.assertLess(report["regions"][0]["contrast_ratio"], 4.5)

    def test_dark_text_on_light_cell_passes(self):
        self._save("#8DBAD5", "#222222")
        report = inspect_text_contrast(self.image, [(70, 45, 170, 90)])
        self.assertTrue(report["ready"], report)
        self.assertGreaterEqual(report["regions"][0]["contrast_ratio"], 4.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
