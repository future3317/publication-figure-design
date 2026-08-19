import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from publication_figure_design.qa.compare import compare_output_to_reference


def test_compare_identical_rasters_is_high(tmp_path):
    image = Image.new("RGB", (120, 80), "white")
    ImageDraw.Draw(image).rectangle((20, 15, 90, 55), fill="#16324F")
    first, second = tmp_path / "a.png", tmp_path / "b.png"
    image.save(first)
    image.save(second)
    report = compare_output_to_reference(first, second)
    assert report["metrics"]["overall_style_similarity"] > 0.95
