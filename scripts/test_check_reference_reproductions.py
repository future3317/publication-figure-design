from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_reference_reproductions import run


class TestReferenceReproductionChecker(unittest.TestCase):
    def test_reviewed_user_reference_requires_figure_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            for name in ("code.py", "reconstruction.png"):
                (root / "assets" / name).write_bytes(b"x")
            (root / "assets" / "registry.jsonl").write_text(
                json.dumps({
                    "id": "ref",
                    "reference_kind": "user_supplied",
                    "review_status": "reviewed",
                    "code_path": "assets/code.py",
                    "reproduction_preview_path": "assets/reconstruction.png",
                }) + "\n",
                encoding="utf-8",
            )

            report = run(root)

            self.assertFalse(report["healthy"])
            self.assertEqual(report["findings"][0]["field"], "figure_card_path")


if __name__ == "__main__":
    unittest.main(verbosity=2)
