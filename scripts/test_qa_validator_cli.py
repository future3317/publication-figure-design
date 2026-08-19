# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qa_validator import validate_source


SCRIPT = Path(__file__).with_name("qa_validator.py")

GOOD_SOURCE = '''
import matplotlib.pyplot as plt
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial"], "font.size": 8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.direction": "out", "legend.frameon": False,
    "pdf.fonttype": 42, "svg.fonttype": "none", "savefig.dpi": 300,
})
COLOR_ROLES = {"context": "#999999", "focus": "#8E5AA7"}
fig, ax = plt.subplots(figsize=(7.2, 4.0))
ax.plot([0, 1], [0, 1], color=COLOR_ROLES["focus"])
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
def save_cns_figure():
    fig.savefig("figure.pdf", dpi=300)
    fig.savefig("figure.png", dpi=300)
'''


class QaValidatorCliTests(unittest.TestCase):
    def test_validate_source_returns_summary(self):
        report = validate_source("print('plain script')")
        self.assertFalse(report["ready"])
        self.assertGreater(report["summary"]["fail"], 0)
        self.assertTrue(report["findings"])

    def test_cli_accepts_inline_source(self):
        run = subprocess.run(
            [sys.executable, str(SCRIPT), "print('inline')"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("Source: <inline>", run.stdout)

    def test_validate_source_has_reachable_ready_state(self):
        report = validate_source(GOOD_SOURCE)
        self.assertTrue(report["ready"], report["findings"])

    def test_heatmap_annotations_require_contrast_safe_helper(self):
        source = GOOD_SOURCE + '''
ax.imshow([[0.1, 0.5], [0.3, 0.9]], cmap="Blues")
ax.text(0, 0, "0.039", color="white")
'''
        report = validate_source(source)
        failures = [item for item in report["findings"] if item["category"] == "FAIL"]
        self.assertTrue(any(item["check_id"] == "CL-8" for item in failures), failures)

    def test_heatmap_fixed_white_text_fails_even_when_helper_is_defined(self):
        source = GOOD_SOURCE + '''
def pick_text_color(background):
    return "#222222"
ax.imshow([[0.1, 0.5], [0.3, 0.9]], cmap="Blues")
ax.text(0, 0, "0.039", color="white")
color = pick_text_color("#ffffff")
'''
        report = validate_source(source)
        failures = [item for item in report["findings"] if item["category"] == "FAIL"]
        self.assertTrue(any(item["check_id"] == "CL-8" for item in failures), failures)

    def test_heatmap_helper_must_be_used_not_only_defined(self):
        source = GOOD_SOURCE + '''
def pick_text_color(background):
    return "#222222"
ax.imshow([[0.1, 0.5], [0.3, 0.9]], cmap="Blues")
ax.text(0, 0, "0.039", color="white")
'''
        report = validate_source(source)
        failures = [item for item in report["findings"] if item["category"] == "FAIL"]
        self.assertTrue(any(item["check_id"] == "CL-8" for item in failures), failures)

    def test_cli_prints_report_and_exits_nonzero_on_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "figure.py"
            source.write_text("print('plain script')\n", encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("Academic Figure Source QA: FIX", run.stdout)
        self.assertIn("[FAIL]", run.stdout)

    def test_cli_writes_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "figure.py"
            output = Path(tmp) / "qa.json"
            source.write_text("print('plain script')\n", encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--json", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(payload["status"], "FIX")
        self.assertGreater(payload["summary"]["fail"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
