import tempfile
import unittest
from pathlib import Path

from publication_figure_design.contracts import TaskSpec
from publication_figure_design.orchestrator.machine import WorkflowStage
from publication_figure_design.orchestrator.runtime import build_runtime_orchestrator


class RuntimeContractTests(unittest.TestCase):
    def test_session_records_input_and_index_provenance(self):
        task = TaskSpec(task_id="resume-test", metadata={"reference_ids": ["a"], "renderer_version": "renderer-test"})
        session = build_runtime_orchestrator().start(task)
        self.assertTrue(session.telemetry["input_hash"])
        self.assertIn("reference_index_version", session.telemetry)
        self.assertEqual(session.telemetry["renderer_version"], "renderer-test")

    def test_reference_led_renderer_must_consume_all_specs(self):
        task = TaskSpec(task_id="render-test", metadata={"reference_led": True, "render_plan": {"consumed_specs": ["PaletteSpec"]}})
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(task)
        while orchestrator.next_stage(session) != WorkflowStage.RENDER and session.status == "ready":
            orchestrator.advance(session)
        orchestrator.advance(session)
        self.assertEqual(session.status, "blocked")
        self.assertIn("TypographySpec", str(session.history[-1]["gate"]))


if __name__ == "__main__":
    unittest.main()
