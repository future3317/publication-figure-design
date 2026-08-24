from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

try:
    from auto_visual_judge import AutoVisualJudge, calibrate, degrade_image, judge_pair
except ModuleNotFoundError:
    from scripts.auto_visual_judge import AutoVisualJudge, calibrate, degrade_image, judge_pair


def response(preferred: str, confidence: float = 0.9) -> dict:
    return {
        "preferred": preferred,
        "confidence": confidence,
        "reason_codes": ["hierarchy", "spacing"],
        "problems": [],
        "repair_needed": False,
    }


class AutoVisualJudgeTests(unittest.TestCase):
    def test_facade_uses_same_consensus_contract(self):
        result = AutoVisualJudge().pair(
            {"display_order": ["a", "b"], "judge": response("A")},
            {"display_order": ["b", "a"], "judge": response("B")},
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["preferred"], "a")

    def test_swapped_order_maps_to_same_candidate(self):
        result = judge_pair(
            {"display_order": ["a", "b"], "judge": response("B")},
            {"display_order": ["b", "a"], "judge": response("A")},
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["preferred"], "b")
        self.assertFalse(result["uncertain"])

    def test_position_disagreement_is_rejected(self):
        result = judge_pair(
            {"display_order": ["a", "b"], "judge": response("B")},
            {"display_order": ["b", "a"], "judge": response("B")},
        )
        self.assertFalse(result["accepted"])
        self.assertTrue(result["uncertain"])
        self.assertIsNone(result["preferred"])

    def test_calibration_requires_correct_and_consistent_judgment(self):
        rows = [
            {
                "original_id": "good",
                "forward": {"display_order": ["good", "bad"], "judge": response("A")},
                "reverse": {"display_order": ["bad", "good"], "judge": response("B")},
            }
        ]
        report = calibrate(rows)
        self.assertTrue(report["passed"])
        self.assertEqual(report["degradation_detection_rate"], 1.0)

    def test_degradation_writer_is_deterministic_and_produces_asset(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            output = Path(directory) / "bad.png"
            Image.new("RGBA", (32, 24), (40, 90, 140, 255)).save(source)
            metadata = degrade_image(source, output, "palette_contrast")
            self.assertTrue(output.is_file())
            self.assertEqual(metadata["degradation_kind"], "palette_contrast")


if __name__ == "__main__":
    unittest.main()
