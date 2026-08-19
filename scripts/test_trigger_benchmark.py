# -*- coding: utf-8 -*-
"""Regression tests for figure-skill dispatch on paired operating-point requests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trigger_benchmark import score_prompt


class TriggerBenchmarkTests(unittest.TestCase):
    def test_paired_operating_point_figure_requests_trigger(self):
        prompts = (
            "plot paired operating points with error bars",
            "make an operating-point comparison for cap 100 vs cap 500",
            "compare accuracy and compute across route states in a figure",
            "redraw the route state operating-points chart",
        )
        for prompt in prompts:
            self.assertGreaterEqual(score_prompt(prompt), 2, prompt)

    def test_algorithm_discussion_without_visual_intent_does_not_trigger(self):
        prompts = (
            "choose the operating point for the optimizer",
            "analyze route-state transitions in the controller",
            "explain the budget-state tradeoff in prose",
        )
        for prompt in prompts:
            self.assertLess(score_prompt(prompt), 2, prompt)


if __name__ == "__main__":
    unittest.main()
