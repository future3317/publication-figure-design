from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from visual_regression import compare, validate_baseline
except ImportError:  # pragma: no cover
    from scripts.visual_regression import compare, validate_baseline

try:
    from freeze_visual_baseline import freeze
except ImportError:  # pragma: no cover
    from scripts.freeze_visual_baseline import freeze


ROOT = Path(__file__).resolve().parents[1]


class VisualRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = json.loads((ROOT / "assets/reference-benchmarks/visual-baseline-v1.json").read_text(encoding="utf-8"))
        self.current = {"tasks": []}
        for row in self.baseline["tasks"]:
            family = row["figure_family"]
            self.current["tasks"].append({
                "id": row["task_id"],
                "figure_family": family,
                "candidate_paths": {f"{family}__balanced": str(ROOT / row["image"])},
                "qa": {f"{family}__balanced": {"L0": {"passed": True}, "L1": {"passed": True}}},
            })

    def test_baseline_contract(self) -> None:
        self.assertEqual(validate_baseline(self.baseline, ROOT), [])

    def test_same_render_is_unchanged(self) -> None:
        report = compare(self.baseline, self.current, {}, ROOT)
        self.assertTrue(report["passed"])
        self.assertEqual(report["overall"]["unchanged"], 25)
        self.assertEqual(report["overall"]["win"], 0)
        self.assertEqual(report["overall"]["loss"], 0)
        self.assertEqual(report["overall"]["uncertain"], 0)

    def test_changed_render_requires_and_accepts_swapped_judge(self) -> None:
        first = self.baseline["tasks"][0]
        family = first["figure_family"]
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as temp:
            changed = Path(temp) / "changed.png"
            shutil.copy2(ROOT / first["image"], changed)
            changed.write_bytes(changed.read_bytes() + b"changed")
            current = json.loads(json.dumps(self.current))
            current["tasks"][0]["candidate_paths"][f"{family}__balanced"] = str(changed)
            judges = {
                first["task_id"]: {
                    "forward": {"display_order": ["baseline", "current"], "judge": {"preferred": "B", "confidence": 0.9, "reason_codes": ["spacing"], "problems": [], "repair_needed": False}},
                    "reverse": {"display_order": ["current", "baseline"], "judge": {"preferred": "A", "confidence": 0.9, "reason_codes": ["spacing"], "problems": [], "repair_needed": False}},
                }
            }
            report = compare(self.baseline, current, judges, ROOT)
            self.assertTrue(report["passed"])
            self.assertEqual(report["overall"]["win"], 1)
            self.assertEqual(report["family_win_rates"][family]["win_rate"], 1.0)

    def test_freezing_a_new_output_does_not_overwrite_existing_baseline(self) -> None:
        report_path = ROOT / "tmp" / "visual_sprint" / "sprint_report.json"
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as temp:
            output = Path(temp) / "visual-baseline-v2.json"
            payload = freeze(report_path.relative_to(ROOT), output.relative_to(ROOT))
            self.assertEqual(payload["baseline_id"], "visual-baseline-v2")
            self.assertTrue(output.is_file())
            self.assertTrue((output.with_suffix("") / "statistical_discovery_01.png").is_file())
            self.assertEqual(validate_baseline(payload, ROOT), [])
            self.assertTrue((ROOT / "assets/reference-benchmarks/visual-baseline-v1.json").is_file())
            with self.assertRaises(FileExistsError):
                freeze(report_path, output)


if __name__ == "__main__":
    unittest.main()
