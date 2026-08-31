import tempfile
import unittest
from pathlib import Path

from publication_figure_design.contracts import (
    LayoutSpec,
    QAReport,
    SourceSpec,
    TaskSpec,
)
from publication_figure_design.orchestrator import GateResult, Orchestrator, WorkflowStage
from publication_figure_design.orchestrator import build_runtime_orchestrator


class OrchestratorTests(unittest.TestCase):
    def test_contracts_are_versioned_and_round_trip(self):
        source = SourceSpec(source_id="s1", data_paths=["data.csv"])
        restored = SourceSpec.from_dict(source.to_dict())
        self.assertEqual(restored.source_id, "s1")
        self.assertEqual(restored.data_paths, ["data.csv"])
        self.assertEqual(LayoutSpec().to_dict()["schema_version"], "1.0")

    def test_gate_blocks_then_retry_resumes(self):
        calls = {"qa": 0}

        def qa(_context):
            calls["qa"] += 1
            return QAReport(passed=calls["qa"] > 1, score=0.8)

        orchestrator = Orchestrator(
            handlers={WorkflowStage.QA: qa},
            gates={WorkflowStage.QA: lambda output: GateResult(output.passed, "QA must pass")},
        )
        session = orchestrator.start(TaskSpec(task_id="t1", objective="test"))
        for _ in range(10):
            orchestrator.advance(session)
        self.assertEqual(session.current_stage, WorkflowStage.REPAIR.value)
        orchestrator.advance(session)  # first QA attempt: blocked
        self.assertEqual(session.status, "blocked")
        self.assertEqual(session.current_stage, WorkflowStage.REPAIR.value)
        orchestrator.retry(session)
        self.assertEqual(session.current_stage, WorkflowStage.QA.value)
        self.assertEqual(session.best_so_far["score"], 0.8)

    def test_rollback_clears_downstream_and_persists(self):
        orchestrator = Orchestrator()
        session = orchestrator.start(TaskSpec(task_id="t2"))
        orchestrator.run(session)
        self.assertTrue(session.is_complete())
        orchestrator.rollback(session, WorkflowStage.RENDER)
        self.assertEqual(session.current_stage, WorkflowStage.BINDING.value)
        self.assertNotIn(WorkflowStage.RENDER.value, session.artifacts)
        self.assertEqual(session.status, "ready")
        with tempfile.TemporaryDirectory() as directory:
            path = session.save(Path(directory) / "session.json")
            loaded = orchestrator.resume(path)
            self.assertEqual(loaded.session_id, "t2")
            self.assertEqual(loaded.current_stage, WorkflowStage.BINDING.value)

    def test_runtime_handlers_materialize_task_metadata(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(
            task_id="runtime",
            metadata={"reference_ids": ["ref-1"], "style_spec_version": "1.0"},
        ))
        orchestrator.run(session)
        self.assertTrue(session.is_complete())
        self.assertEqual(session.telemetry["reference_ids"], ["ref-1"])
        self.assertEqual(session.artifacts[WorkflowStage.REFERENCE_RETRIEVAL.value]["payload"]["status"], "ready")

    def test_domain_profile_is_loaded_into_design_spec(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(
            task_id="domain-run",
            metadata={"domain": "ml-ai", "journal": "generic"},
        ))
        orchestrator.run(session)
        self.assertTrue(session.is_complete())
        design = session.artifacts[WorkflowStage.DESIGN_SPEC.value]["payload"]
        self.assertIn("domain_profile", design)
        self.assertEqual(design["domain_profile"]["domain"], "ml-ai")
        packet = design["design_packet"]
        self.assertEqual(packet["domain_profile"]["domain"], "ml-ai")
        self.assertTrue(any("preferred_family:comparison_effect" in c for c in packet["domain_constraints_applied"]))
        self.assertIn("tripod-ai", packet["domain_source_ids"])


if __name__ == "__main__":
    unittest.main()
