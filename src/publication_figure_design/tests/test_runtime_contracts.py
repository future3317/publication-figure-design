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

    def test_production_runtime_allows_only_one_repair_retry(self):
        self.assertEqual(build_runtime_orchestrator().max_retries, 2)

    def test_reference_led_renderer_must_consume_all_specs(self):
        task = TaskSpec(task_id="render-test", metadata={"reference_led": True, "render_plan": {"consumed_specs": ["PaletteSpec"]}})
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(task)
        while orchestrator.next_stage(session) != WorkflowStage.RENDER and session.status == "ready":
            orchestrator.advance(session)
        orchestrator.advance(session)
        self.assertEqual(session.status, "blocked")
        self.assertIn("TypographySpec", str(session.history[-1]["gate"]))

    def test_reference_selection_telemetry_records_roles_top_k_and_family(self):
        task = TaskSpec(
            task_id="retrieval-telemetry",
            metadata={
                "figure_family": "matrix_array",
                "reference_set": {
                    "structure_reference": "structure-1",
                    "style_reference": "style-1",
                    "component_references": ["component-1"],
                    "annotation_reference": "annotation-1",
                    "palette_reference": "palette-1",
                    "candidates": [{"id": "structure-1"}, {"id": "structure-2"}],
                },
            },
        )
        session = build_runtime_orchestrator().run(build_runtime_orchestrator().start(task))
        telemetry = session.telemetry
        self.assertEqual(telemetry["task_id"], "retrieval-telemetry")
        self.assertEqual(telemetry["figure_family"], "matrix_array")
        self.assertEqual(telemetry["selected_reference_ids"], ["annotation-1", "component-1", "palette-1", "structure-1", "style-1"])
        self.assertEqual(telemetry["top_k_ids"], ["structure-1", "structure-2"])
        self.assertEqual(telemetry["selected_roles"], {
            "structure_reference": ["structure-1"],
            "style_reference": ["style-1"],
            "component_references": ["component-1"],
            "annotation_reference": ["annotation-1"],
            "palette_reference": ["palette-1"],
        })


if __name__ == "__main__":
    unittest.main()
