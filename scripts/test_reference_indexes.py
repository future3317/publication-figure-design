import json
import tempfile
import unittest
from pathlib import Path

from build_reference_indexes import build_indexes


class ReferenceIndexTests(unittest.TestCase):
    def test_builds_role_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = root / "assets" / "visual-references" / "references" / "abc" / "metadata.json"
            metadata.parent.mkdir(parents=True)
            metadata.write_text(json.dumps({"id": "abc", "scope": "references", "figure_type": "scatter", "tags": ["hero"], "visual_grammar": {"palette_roles": {"background": "white"}}}), encoding="utf-8")
            report = build_indexes(root)
            self.assertEqual(report["records"], 1)
            payload = json.loads((root / "indexes" / "style.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertIn("abc", payload["records"])
            self.assertEqual(payload["aliases"]["current"], payload["model_version"])
            self.assertEqual(len(payload["provenance"]["corpus_sha256"]), 64)
            semantic = json.loads((root / "indexes" / "semantic.json").read_text(encoding="utf-8"))
            self.assertEqual(semantic["index_type"], "semantic_proxy")
            self.assertEqual(len(semantic["records"]["abc"]["vector"]), 4)
            self.assertTrue(semantic["records"]["abc"]["model_version"].startswith("deterministic-proxy-"))


if __name__ == "__main__":
    unittest.main()
