from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image

try:
    import run_visual_sprint as sprint
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts import run_visual_sprint as sprint


class VisualSprintTests(unittest.TestCase):
    def test_source_variants_do_not_emit_synthetic_preferences(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            Image.new("RGB", (120, 80), "white").save(source)
            task = {
                "id": "calibration_case",
                "figure_family": "statistical_discovery",
                "figure_type": "scatter",
                "source_image": str(source),
                "source_code": "",
            }

            row = sprint._run_task(task, root / "task")

        self.assertEqual(row["generation_method"], "source_render_variant")
        self.assertNotIn("pairwise", row)
        self.assertNotIn("judge", row)

    def test_main_preserves_unrelated_files_in_its_output_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            Image.new("RGB", (32, 24), "white").save(source)
            manifest = root / "tasks.json"
            manifest.write_text(json.dumps({
                "tasks": [
                    {
                        "id": f"task_{index:02}",
                        "figure_family": "statistical_discovery",
                        "figure_type": "scatter",
                        "source_image": str(source),
                        "source_code": "",
                    }
                    for index in range(25)
                ]
            }), encoding="utf-8")
            output_root = root / "visual_sprint"
            output_root.mkdir()
            unrelated = output_root / "keep.txt"
            unrelated.write_text("local evidence", encoding="utf-8")

            with patch.object(sprint, "MANIFEST", manifest), patch.object(sprint, "OUT_ROOT", output_root), patch.object(sys, "argv", ["run_visual_sprint.py"]):
                result = sprint.main()

            self.assertEqual(result, 0)
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "local evidence")


if __name__ == "__main__":
    unittest.main()
