import json
import tempfile
import unittest
from pathlib import Path

from evaluate_benchmark import evaluate


class BenchmarkEvaluationTests(unittest.TestCase):
    def test_reports_retrieval_and_generation_metrics(self):
        path = Path(__file__).resolve().parents[1] / "assets" / "reference-benchmarks" / "golden_tasks.json"
        report = evaluate(path)
        self.assertEqual(report["golden_task_count"], 3)
        self.assertEqual(report["retrieval_summary"]["recall_at_1"], 1.0)
        self.assertGreater(report["retrieval_summary"]["ndcg_at_3"], 0.9)
        self.assertIn("reference_alignment", report["generation_summary"])

    def test_empty_benchmark_is_well_formed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.json"
            path.write_text(json.dumps({"tasks": [], "generation": []}), encoding="utf-8")
            report = evaluate(path)
        self.assertEqual(report["retrieval_summary"]["recall_at_3"], 0.0)
        self.assertEqual(report["generation_summary"]["export"], 0.0)


if __name__ == "__main__":
    unittest.main()
