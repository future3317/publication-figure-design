from __future__ import annotations

import unittest
from unittest.mock import patch

try:
    import ci_gate
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts import ci_gate


class CiGateTests(unittest.TestCase):
    def test_visual_gate_validates_checkpoint_without_rendering_local_source_variants(self):
        with patch.object(ci_gate, "run_step") as run_step:
            ci_gate.run_visual_regression_gate()

        run_step.assert_called_once_with(
            "visual baseline contract",
            ["scripts/visual_regression.py", "--contract-only"],
        )


if __name__ == "__main__":
    unittest.main()
