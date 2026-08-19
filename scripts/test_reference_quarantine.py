import json
import shutil
import tempfile
import unittest
from pathlib import Path

from reference_library import ReferenceLibrary


REVIEW = {
    "final_size_inspected": True,
    "hierarchy": "pass",
    "panel_balance": "pass",
    "whitespace": "pass",
    "legend_footprint": "pass",
    "text_legibility": "pass",
    "reviewer": "quarantine-test",
}


class QuarantineTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="pfd-quarantine-"))
        (self.root / "SKILL.md").write_text("# skill\n", encoding="utf-8")
        self.lib = ReferenceLibrary(root=self.root)
        image = self.root / "figure.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 16)
        self.ref = self.lib.ingest(image, "GroupedBar")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_raw_reviewed_benchmarked_production_transitions(self):
        self.assertEqual(self.ref.metadata["lifecycle_state"], "raw")
        self.lib.review(self.ref.id, 4.5, REVIEW)
        self.assertEqual(self.ref.metadata["lifecycle_state"], "reviewed")
        self.lib.benchmark_reference(self.ref.id, {"canary_pass": True})
        self.assertEqual(self.ref.metadata["lifecycle_state"], "benchmarked")
        self.lib.promote_reference(self.ref.id, {"champion_floor_pass": True})
        self.assertTrue(self.ref.metadata["production_ready"])
        self.assertEqual(self.ref.metadata["lifecycle_state"], "production")

    def test_strict_recommendation_excludes_reviewed_until_benchmark(self):
        self.lib.review(self.ref.id, 4.5, REVIEW)
        self.assertEqual(self.lib.recommend_candidates("GroupedBar", require_benchmark=True)["candidates"], [])


if __name__ == "__main__":
    unittest.main()
