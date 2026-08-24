from __future__ import annotations

import json
import unittest
from pathlib import Path

try:
    from champion_board import _validate_board, build_report
except ModuleNotFoundError:  # direct module invocation from repository root
    from scripts.champion_board import _validate_board, build_report


ROOT = Path(__file__).resolve().parents[1]


class ChampionBoardTests(unittest.TestCase):
    def test_board_contract_covers_taxonomy(self):
        board = json.loads((ROOT / "assets/reference-benchmarks/champion_board.json").read_text(encoding="utf-8"))
        self.assertEqual(_validate_board(board), [])

    def test_report_exposes_quality_and_diversity_gaps(self):
        board = json.loads((ROOT / "assets/reference-benchmarks/champion_board.json").read_text(encoding="utf-8"))
        report = build_report(ROOT, board)
        self.assertEqual(report["summary"]["family_count"], len(board["families"]))
        self.assertGreaterEqual(report["summary"]["preference_pair_count"], 2)
        row = next(item for item in report["families"] if item["id"] == "comparison_effect")
        self.assertIn("quality_score", row)
        self.assertIn("diversity_score", row)
        self.assertIn("direct_label_or_legendless", row["gaps"])
        self.assertEqual(row["status"], "needs_evidence")

    def test_focus_sprint_is_five_families_and_not_ready_without_evidence(self):
        board = json.loads((ROOT / "assets/reference-benchmarks/champion_board.json").read_text(encoding="utf-8"))
        report = build_report(ROOT, board)
        self.assertEqual(report["summary"]["focus_family_count"], 5)
        self.assertEqual(report["summary"]["focus_ready_family_count"], 0)
        focus_rows = [row for row in report["families"] if row["focus"]]
        self.assertEqual(len(focus_rows), 5)
        self.assertTrue(all(row["status"] == "needs_evidence" for row in focus_rows))


if __name__ == "__main__":
    unittest.main()
