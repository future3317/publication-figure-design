from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_generated_reproductions import check_record_paths, _sync_source_manifest_hashes


class TestGeneratedReproductionAudit(unittest.TestCase):
    def test_sync_updates_source_manifest_output_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "assets" / "visual-references" / "generated-archive" / "abc" / "image.png"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"fresh-preview")
            manifest = root / "assets" / "visual-references" / "source-reconstruction-manifest.json"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(json.dumps({"records": [{
                "image_path": "assets/visual-references/generated-archive/abc/image.png",
                "output_sha256": "stale",
            }]}), encoding="utf-8")

            self.assertEqual(_sync_source_manifest_hashes(root), 1)
            updated = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(updated["records"][0]["output_sha256"],
                             __import__("hashlib").sha256(b"fresh-preview").hexdigest())

    def test_record_requires_code_preview_and_figure_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset = root / "assets" / "visual-references" / "generated-archive" / "abc"
            asset.mkdir(parents=True)
            (asset / "code.py").write_text("# render\n", encoding="utf-8")
            (asset / "image.png").write_bytes(b"not-an-image")
            metadata = {
                "id": "abc",
                "scope": "generated-archive",
                "image_path": "assets/visual-references/generated-archive/abc/image.png",
                "code_path": "assets/visual-references/generated-archive/abc/code.py",
            }

            findings = check_record_paths(root, metadata)

            self.assertIn("reproduction_preview_path", findings)
            self.assertIn("figure_card_path", findings)

    def test_complete_record_has_no_path_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset = root / "assets" / "visual-references" / "generated-archive" / "abc"
            asset.mkdir(parents=True)
            for name in ("code.py", "image.png", "figure_card.json"):
                (asset / name).write_text("{}", encoding="utf-8")
            metadata = {
                "id": "abc",
                "scope": "generated-archive",
                "image_path": "assets/visual-references/generated-archive/abc/image.png",
                "code_path": "assets/visual-references/generated-archive/abc/code.py",
                "reproduction_preview_path": "assets/visual-references/generated-archive/abc/image.png",
                "figure_card_path": "assets/visual-references/generated-archive/abc/figure_card.json",
            }

            self.assertEqual(check_record_paths(root, metadata), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
