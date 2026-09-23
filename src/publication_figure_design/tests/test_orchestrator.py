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
    def test_create_route_skips_reference_stages_when_no_reference_is_supplied(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(task_id="create-no-reference"))

        stages = session.route_plan.stages
        self.assertNotIn(WorkflowStage.REFERENCE_RETRIEVAL.value, stages)
        self.assertNotIn(WorkflowStage.REFERENCE_INSPECTION.value, stages)
        self.assertNotIn(WorkflowStage.COMPARE.value, stages)

    def test_reference_presence_inserts_reference_stages_once(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(
            task_id="create-with-reference",
            metadata={"reference_ids": ["ref-1"]},
        ))

        stages = session.route_plan.stages
        self.assertEqual(stages.count(WorkflowStage.REFERENCE_RETRIEVAL.value), 1)
        self.assertEqual(stages.count(WorkflowStage.REFERENCE_INSPECTION.value), 1)
        self.assertEqual(stages.count(WorkflowStage.COMPARE.value), 1)

    def test_review_route_uses_only_review_stages(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(task_id="review-route", mode="review"))

        self.assertEqual(session.route_plan.stages, [
            WorkflowStage.ROUTE.value,
            WorkflowStage.INTAKE.value,
            WorkflowStage.QA.value,
        ])

    def test_visual_optimization_alias_uses_revise_workflow(self):
        session = build_runtime_orchestrator().start(TaskSpec(
            task_id="optimization-alias",
            metadata={"route": "visual_optimization"},
        ))

        self.assertEqual(session.route_plan.mode, "revise")
        self.assertEqual(session.route_plan.stages[0], WorkflowStage.ROUTE.value)

    def test_unknown_route_fails_instead_of_silently_becoming_create(self):
        with self.assertRaisesRegex(ValueError, "Unknown workflow route 'revieew'"):
            build_runtime_orchestrator().start(TaskSpec(
                task_id="unknown-route",
                metadata={"route": "revieew"},
            ))

    def test_route_plan_cursor_resumes_repeated_stages_deterministically(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(task_id="repeat-route"))
        session.route_plan.stages = [
            WorkflowStage.ROUTE.value,
            WorkflowStage.RENDER.value,
            WorkflowStage.QA.value,
            WorkflowStage.RENDER.value,
            WorkflowStage.QA.value,
        ]
        session.route_plan.cursor = 2
        restored = orchestrator.resume(session.to_dict())

        self.assertEqual(orchestrator.next_stage(restored), WorkflowStage.RENDER)

    def test_qa_failure_inserts_one_repair_cycle_before_export(self):
        calls = {"qa": 0}

        def qa(_context):
            calls["qa"] += 1
            return {"status": "ready", "errors": []} if calls["qa"] > 1 else {"status": "blocked", "errors": ["label overlap in panel B"]}

        orchestrator = build_runtime_orchestrator()
        orchestrator.handlers[WorkflowStage.QA.value] = qa
        session = orchestrator.start(TaskSpec(task_id="qa-repair-route"))
        while orchestrator.next_stage(session) != WorkflowStage.QA and session.status == "ready":
            orchestrator.advance(session)
        orchestrator.advance(session)

        self.assertEqual(session.status, "ready")
        self.assertEqual(orchestrator.next_stage(session), WorkflowStage.CRITIQUE)
        self.assertEqual(session.route_plan.applied_conditions, ["qa_failed"])
        self.assertEqual(session.route_plan.stages.count(WorkflowStage.QA.value), 2)
        self.assertEqual(session.telemetry["policy_packet"]["qa_feedback"], ["label overlap in panel B"])

    def test_qa_repair_waits_for_patch_then_resumes(self):
        calls = {"qa": 0}

        def qa(_context):
            calls["qa"] += 1
            return {"status": "blocked", "errors": ["legend overlaps plot"]} if calls["qa"] == 1 else {"status": "ready", "errors": []}

        orchestrator = build_runtime_orchestrator()
        orchestrator.handlers[WorkflowStage.QA.value] = qa
        session = orchestrator.start(TaskSpec(task_id="qa-awaits-patch"))
        orchestrator.run(session)

        self.assertEqual(session.status, "blocked")
        self.assertEqual(session.current_stage, WorkflowStage.CRITIQUE.value)
        self.assertEqual(orchestrator.next_stage(session), WorkflowStage.CRITIQUE)
        self.assertIn("legend overlaps plot", session.telemetry["policy_packet"]["qa_feedback"])

        session.task["metadata"]["design_patch"] = {"patches": [{"op": "adjust_legend", "target": "figure"}]}
        orchestrator.retry(session)
        orchestrator.run(session)
        self.assertTrue(session.is_complete())
        self.assertEqual(calls["qa"], 2)

    def test_route_plan_is_preserved_in_session_json(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(task_id="route-plan-round-trip"))
        restored = orchestrator.resume(session.to_dict())

        self.assertEqual(restored.route_plan.to_dict(), session.route_plan.to_dict())

    def test_pre_route_plan_session_resumes_on_its_original_stage_order(self):
        orchestrator = build_runtime_orchestrator()
        legacy = {
            "session_id": "legacy-session",
            "task": TaskSpec(task_id="legacy-session").to_dict(),
            "current_stage": WorkflowStage.BINDING.value,
            "status": "ready",
            "telemetry": {},
        }

        restored = orchestrator.resume(legacy)

        self.assertEqual(orchestrator.next_stage(restored), WorkflowStage.RENDER)
        self.assertEqual(restored.route_plan.mode, "legacy_resume")

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
        orchestrator.run(session)
        self.assertTrue(session.is_complete())
        executed = [record["stage"] for record in session.history]
        self.assertIn(WorkflowStage.CRITIQUE.value, executed)
        self.assertIn(WorkflowStage.REPAIR.value, executed)
        self.assertEqual(executed.count(WorkflowStage.QA.value), 2)
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
        self.assertEqual(session.status, "blocked")
        self.assertEqual(session.telemetry["reference_ids"], ["ref-1"])
        self.assertEqual(session.artifacts[WorkflowStage.REFERENCE_RETRIEVAL.value]["payload"]["status"], "ready")

    def test_domain_profile_is_loaded_into_design_spec(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(
            task_id="domain-run",
            metadata={"domain": "ml-ai", "journal": "generic"},
        ))
        while orchestrator.next_stage(session) != WorkflowStage.DESIGN_SPEC:
            orchestrator.advance(session)
        orchestrator.advance(session)
        design = session.artifacts[WorkflowStage.DESIGN_SPEC.value]["payload"]
        self.assertIn("domain_profile", design)
        self.assertEqual(design["domain_profile"]["domain"], "ml-ai")
        packet = design["design_packet"]
        self.assertEqual(packet["domain_profile"]["domain"], "ml-ai")
        self.assertTrue(any("preferred_family:comparison_effect" in c for c in packet["domain_constraints_applied"]))
        self.assertIn("tripod-ai", packet["domain_source_ids"])


if __name__ == "__main__":
    unittest.main()
