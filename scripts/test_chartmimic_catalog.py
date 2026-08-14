from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chartmimic_catalog import build_catalog


class TestChartMimicCatalog(unittest.TestCase):
    def test_build_catalog_extracts_code_and_dimensions_without_copying_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "dimentions_info.jsonl"
            output = root / "catalog.json"
            source.write_text(
                json.dumps({"file": "bar_1.py", "code": "import matplotlib.pyplot as plt\n", "width": 4.0, "height": 3.0, "idx": "bar_1"})
                + "\n"
                + json.dumps({"file": "line_1.py", "code": "plt.plot([1, 2])\n", "width": 5.0, "height": 2.5, "idx": "line_1"})
                + "\n",
                encoding="utf-8",
            )

            catalog = build_catalog(source, output)

            self.assertEqual(catalog["source"]["name"], "ChartMimic")
            self.assertEqual(catalog["count"], 2)
            self.assertEqual(catalog["items"][0]["id"], "bar_1")
            self.assertEqual(catalog["items"][0]["code_path"], "dimentions_info.jsonl#bar_1")
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
