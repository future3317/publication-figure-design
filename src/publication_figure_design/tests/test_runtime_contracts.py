import unittest
import tempfile
from pathlib import Path

from publication_figure_design.contracts import TaskSpec
from publication_figure_design.orchestrator.machine import WorkflowStage
from publication_figure_design.orchestrator.runtime import build_runtime_orchestrator
from publication_figure_design.orchestrator.runtime import _qa
from publication_figure_design.orchestrator.machine import StageContext
from publication_figure_design.qa.technical import run_hard_qa


class RuntimeContractTests(unittest.TestCase):
    def test_session_records_input_and_index_provenance(self):
        task = TaskSpec(task_id="resume-test", metadata={"reference_ids": ["a"], "renderer_version": "renderer-test"})
        session = build_runtime_orchestrator().start(task)
        self.assertTrue(session.telemetry["input_hash"])
        self.assertIn("reference_index_version", session.telemetry)
        self.assertEqual(session.telemetry["renderer_version"], "renderer-test")

    def test_session_compiles_active_rule_sets(self):
        task = TaskSpec(task_id="rules-test", metadata={"mode": "create"})
        session = build_runtime_orchestrator().start(task)
        self.assertIn("active_rule_sets", session.telemetry)
        self.assertIn("rules/global/scientific-integrity.yaml", session.telemetry["active_rule_sets"])
        self.assertIn("SCI-001", session.telemetry["active_rule_ids"])
        self.assertIn("policy_packet", session.telemetry)
        self.assertIn("hard_constraints", session.telemetry["policy_packet"])
        self.assertIn("style_tokens", session.telemetry["policy_packet"])

    def test_session_adds_family_rules(self):
        task = TaskSpec(task_id="family-rules-test", metadata={"mode": "create", "figure_family": "heatmap"})
        session = build_runtime_orchestrator().start(task)
        self.assertIn("rules/families/heatmap-matrix.yaml", session.telemetry["active_rule_sets"])
        self.assertIn("HEAT-001", session.telemetry["active_rule_ids"])
        self.assertTrue(any(item.startswith("HEAT-001:") for item in session.telemetry["policy_packet"]["family_constraints"]))

    def test_session_adds_curve_feedback_rules(self):
        task = TaskSpec(task_id="curve-rules-test", metadata={"mode": "create", "figure_family": "curve_comparison"})
        session = build_runtime_orchestrator().start(task)
        self.assertIn("rules/families/curve-comparison.yaml", session.telemetry["active_rule_sets"])
        self.assertIn("CURVE-001", session.telemetry["active_rule_ids"])

    def test_session_adds_inset_feedback_rules(self):
        task = TaskSpec(task_id="inset-rules-test", metadata={"mode": "create", "figure_family": "inset_comparison"})
        session = build_runtime_orchestrator().start(task)
        self.assertIn("rules/families/multi-panel-composite.yaml", session.telemetry["active_rule_sets"])
        self.assertIn("MP-004", session.telemetry["active_rule_ids"])

    def test_session_adds_bar_feedback_rules(self):
        task = TaskSpec(task_id="bar-rules-test", metadata={"mode": "create", "figure_family": "bars_and_intervals"})
        session = build_runtime_orchestrator().start(task)
        self.assertIn("rules/families/bars-and-intervals.yaml", session.telemetry["active_rule_sets"])
        self.assertIn("BAR-001", session.telemetry["active_rule_ids"])

    def test_session_compiles_tex_backend_rules(self):
        task = TaskSpec(task_id="tex-rules-test", metadata={"mode": "tex_backend", "route": "tex_backend", "backend": "tex"})
        session = build_runtime_orchestrator().start(task)
        self.assertIn("rules/backend/tex.yaml", session.telemetry["active_rule_sets"])
        self.assertIn("TEX-001", session.telemetry["active_rule_ids"])

    def test_production_runtime_allows_only_one_repair_retry(self):
        self.assertEqual(build_runtime_orchestrator().max_retries, 2)

    def test_production_design_defaults_to_one_candidate(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(
            task_id="one-production-candidate",
            metadata={"source": {"source_id": "source"}},
        ))
        while orchestrator.next_stage(session) != WorkflowStage.DESIGN_SPEC and session.status == "ready":
            orchestrator.advance(session)
        orchestrator.advance(session)

        packet = session.artifacts[WorkflowStage.DESIGN_SPEC.value]["payload"]["design_packet"]
        self.assertEqual(len(packet["candidates"]), 1)

    def test_evaluation_mode_keeps_three_candidates(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(
            task_id="three-evaluation-candidates",
            metadata={"generation_mode": "evaluation"},
        ))
        while orchestrator.next_stage(session) != WorkflowStage.DESIGN_SPEC and session.status == "ready":
            orchestrator.advance(session)
        orchestrator.advance(session)

        packet = session.artifacts[WorkflowStage.DESIGN_SPEC.value]["payload"]["design_packet"]
        self.assertEqual(len(packet["candidates"]), 3)

    def test_structural_comparison_is_optional_without_a_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            figure = Path(tmp) / "figure.png"
            figure.write_bytes(b"rendered-figure")
            result = _qa(StageContext(
                session_id="qa-no-reference",
                stage=WorkflowStage.QA.value,
                task={"metadata": {"candidate_image": str(figure), "design_packet": {
                    "style_tokens": {"foreground": "#222222"},
                    "journal_profile": {"name": "generic", "status": "verified", "verified": True},
                    "scientific_contract": {"data": "bound"},
                }, "render_trace": {"artists": [{"type": "line"}]}}},
                contracts={},
                artifacts={},
            ))

        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["structural"]["status"], "not_applicable")

    def test_review_without_a_figure_blocks_without_entering_render_repair(self):
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(TaskSpec(task_id="review-missing-figure", mode="review"))

        orchestrator.run(session)

        self.assertEqual(session.status, "blocked")
        self.assertEqual(session.current_stage, WorkflowStage.QA.value)
        self.assertNotIn(WorkflowStage.CRITIQUE.value, session.route_plan.stages)

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

    def test_placeholder_journal_profile_blocks_technical_certification(self):
        report = run_hard_qa(__file__, {"journal_profile": {"name": "science", "status": "placeholder"}})
        self.assertFalse(report["passed"])
        self.assertTrue(any("placeholder" in issue for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
