# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
import subprocess
import sys
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
    "reviewer": "candidate recommender test",
}


class CandidateRecommenderTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="afs_candidates_"))
        (self.root / "SKILL.md").write_text("# skill\n", encoding="utf-8")
        self.lib = ReferenceLibrary(root=self.root)
        self.serial = 0

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def add(self, figure_type, rating=4, **metadata):
        self.serial += 1
        image = self.root / f"image-{self.serial}.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([self.serial]) * 8)
        ref = self.lib.ingest(image, figure_type, metadata_override=metadata)
        return self.lib.review(ref.id, rating, REVIEW)

    def test_figure_type_is_required(self):
        with self.assertRaises(ValueError):
            self.lib.recommend_candidates(figure_type="")

    def test_grouped_bar_alias_matches_bar_comparison(self):
        ref = self.add("BarComparison")
        report = self.lib.recommend_candidates("GroupedBar")
        self.assertEqual(report["candidates"][0]["id"], ref.id)

    def test_different_figure_types_get_different_shortlists(self):
        heatmap = self.add("Heatmap", rating=5)
        line = self.add("LineTrend", rating=3)
        heatmap_report = self.lib.recommend_candidates("Heatmap")
        line_report = self.lib.recommend_candidates("LineTrend")
        self.assertEqual([c["id"] for c in heatmap_report["candidates"]], [heatmap.id])
        self.assertEqual([c["id"] for c in line_report["candidates"]], [line.id])

    def test_preferred_task_match_outranks_higher_aesthetic_rating(self):
        generic = self.add("Heatmap", rating=5, tags=["dense"], layout="1x1")
        matching = self.add("Heatmap", rating=3.5, tags=["correlation"], layout="2x2")
        report = self.lib.recommend_candidates(
            "Heatmap", preferred_tags=["correlation"], layout="2x2"
        )
        self.assertEqual(report["candidates"][0]["id"], matching.id)
        self.assertNotEqual(report["candidates"][0]["id"], generic.id)

    def test_required_tags_are_hard_filters(self):
        self.add("GroupedBar", tags=["annotation"])
        required = self.add("GroupedBar", tags=["annotation", "individual-points"])
        report = self.lib.recommend_candidates(
            "GroupedBar", required_tags=["individual-points"]
        )
        self.assertEqual([c["id"] for c in report["candidates"]], [required.id])

    def test_shortlist_diversifies_subtype_and_source(self):
        first = self.add(
            "LineTrend", rating=5, subtype="smooth", layout="1x1", source="collection-a"
        )
        near_duplicate = self.add(
            "LineTrend", rating=4.9, subtype="smooth", layout="1x1", source="collection-a"
        )
        diverse = self.add(
            "LineTrend", rating=4.4, subtype="faceted", layout="1x3", source="collection-b"
        )
        report = self.lib.recommend_candidates("LineTrend", limit=2)
        ids = [candidate["id"] for candidate in report["candidates"]]
        self.assertEqual(ids[0], first.id)
        self.assertIn(diverse.id, ids)
        self.assertNotIn(near_duplicate.id, ids)

    def test_excluded_ids_are_not_returned(self):
        first = self.add("PCA", rating=5)
        second = self.add("PCA", rating=4)
        report = self.lib.recommend_candidates("PCA", exclude_ids=[first.id])
        self.assertEqual([c["id"] for c in report["candidates"]], [second.id])

    def test_report_explains_matches_cautions_and_shortage(self):
        self.add("Heatmap", rating=4, tags=["dense"], layout="1x1", data_density="high")
        report = self.lib.recommend_candidates(
            "Heatmap", preferred_tags=["correlation"], layout="2x2", limit=3
        )
        self.assertEqual(report["status"], "insufficient_pool")
        self.assertTrue(report["insufficient_pool"])
        self.assertEqual(report["requested_limit"], 3)
        candidate = report["candidates"][0]
        self.assertIn("exact figure type", " ".join(candidate["matches"]).lower())
        self.assertIn("layout", " ".join(candidate["cautions"]).lower())
        self.assertIn("preferred tag", " ".join(candidate["cautions"]).lower())

    def test_cli_recommend_writes_json_report(self):
        self.add("Heatmap", tags=["correlation"], layout="2x2")
        output = self.root / "recommendation.json"
        run = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("reference_library.py")),
                "recommend",
                "--figure-type", "Heatmap",
                "--preferred-tags", "correlation",
                "--layout", "2x2",
                "--limit", "3",
                "--json", str(output),
                "--root", str(self.root),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["request"]["figure_type"], "heatmap_grid")
        self.assertEqual(len(report["candidates"]), 1)

    def test_recommendation_deduplicates_duplicate_metadata_pixels(self):
        first = self.add("LineTrend", rating=5, subtype="smooth", source="a")
        duplicate_dir = self.root / "assets" / "visual-references" / "references" / "duplicate"
        duplicate_dir.mkdir(parents=True)
        image_path = first.image_path
        duplicate_image = duplicate_dir / "image.png"
        duplicate_image.write_bytes(image_path.read_bytes())
        metadata = dict(first.metadata)
        metadata.update({"id": "duplicate", "image_path": duplicate_image.relative_to(self.root).as_posix()})
        (duplicate_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        report = ReferenceLibrary(root=self.root).recommend_candidates("LineTrend", limit=3)
        self.assertEqual(len(report["candidates"]), 1)
        self.assertIn(report["candidates"][0]["id"], {first.id, "duplicate"})

    def test_recommendation_excludes_missing_reviewed_image(self):
        ref = self.add("PCA", rating=5)
        ref.image_path.unlink()
        report = ReferenceLibrary(root=self.root).recommend_candidates("PCA")
        self.assertEqual(report["candidates"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
