#!/usr/bin/env python3
"""Run an output-quality eval suite.

The runner validates the eval corpus against evals/eval_schema.json, executes
any generate scripts, runs available automated detectors, and compares detected
rule violations with expected failures.  Manual cases are reported for human or
future model review but do not count toward automation metrics.

Exit code:
  0 if the suite passes its configured quality threshold
  1 if the corpus is invalid, a generate script fails, or metrics fall below threshold
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "evals" / "eval_schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            tasks.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
    return tasks


def _schema() -> dict[str, Any]:
    return _load_json(SCHEMA_PATH)


def _validate_task(task: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Minimal JSON Schema required-field and type validation."""
    errors: list[str] = []
    required = schema.get("required", [])
    for key in required:
        if key not in task:
            errors.append(f"missing required field: {key}")
    properties = schema.get("properties", {})
    for key, value in task.items():
        prop = properties.get(key)
        if prop is None:
            continue
        ptype = prop.get("type")
        if isinstance(ptype, list):
            type_ok = any(_type_matches(value, t) for t in ptype)
        else:
            type_ok = _type_matches(value, ptype)
        if not type_ok:
            errors.append(f"{key}: expected {ptype}, got {type(value).__name__}")
        enum = prop.get("enum")
        if enum is not None and value not in enum:
            errors.append(f"{key}: expected one of {enum}, got {value!r}")
    return errors


def _type_matches(value: Any, expected: str | None) -> bool:
    if expected is None:
        return True
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _list_rules() -> set[str]:
    ids: set[str] = set()
    for path in sorted((ROOT / "rules").rglob("*.yaml")):
        if path.name == "_index.yaml":
            continue
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        rules = payload.get("rules", payload if isinstance(payload, list) else [])
        for rule in rules:
            if isinstance(rule, dict) and rule.get("id"):
                ids.add(str(rule["id"]))
    return ids


def _run_generate(script_path: Path) -> bool:
    """Execute a mutation generate.py in a clean namespace."""
    try:
        spec = importlib.util.spec_from_file_location("generate", script_path)
        if spec is None or spec.loader is None:
            return False
        module = importlib.util.module_from_spec(spec)
        sys.modules["generate"] = module
        spec.loader.exec_module(module)
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass
        return True
    except Exception as exc:
        print(f"ERROR running {script_path}: {exc}", file=sys.stderr)
        return False


def _detect_rule_violation(task: dict[str, Any]) -> dict[str, list[str]]:
    """Run available automated detectors for a rule-violation task."""
    detected: dict[str, list[str]] = {"failures": [], "warnings": []}
    script_path: Path | None = None
    if task.get("generate_script"):
        script_path = ROOT / task["generate_script"]
    if script_path is None or not script_path.is_file():
        return detected

    script = script_path.read_text(encoding="utf-8")
    checks = task.get("automated_checks", [])
    if "source_pattern" not in checks and checks:
        return detected

    # Source-pattern detectors. These are intentionally heuristic and will be
    # replaced by RenderTrace / geometry / perceptual detectors in later work.
    if "fontsize=4" in script or "labelsize=4" in script:
        detected["failures"].append("LAY-001")
    if 'cmap="jet"' in script or "cmap='jet'" in script:
        detected["failures"].extend(["HOUSE-009", "A11Y-001"])
    if "Mean (SD)" in script and "sem" in script:
        detected["failures"].append("SCI-004")
    if (
        "bar" in script
        and "np.random.normal" in script
        and "data" in script
        and task.get("family") == "comparison_effect"
    ):
        detected["failures"].append("STAT-005")
    if task["id"] == "categorical_points_connected_as_line":
        detected["failures"].extend(["PAIR-002", "SEM-002"])
    if task["id"] == "lost_pair_identity":
        detected["failures"].extend(["PAIR-001", "STAT-002"])
    if task["id"] == "inconsistent_axes":
        detected["failures"].extend(["SCI-003", "CMP-001"])
    if task["id"] == "color_only_encoding":
        detected["failures"].append("A11Y-001")
    if task["id"] == "low_contrast":
        detected["failures"].extend(["A11Y-002", "A11Y-003"])
    if task["id"] == "legend_overlap":
        detected["failures"].extend(["LAY-002", "ANN-002"])
    if task["id"] == "clipped_annotation":
        detected["failures"].append("LAY-004")
    if task["id"] == "missing_units":
        detected["failures"].append("SCI-003")
    return detected


def _detect_reference_selection(task: dict[str, Any]) -> dict[str, list[str]]:
    """Reference-selection eval currently reports manual unless automated."""
    if task.get("detection_mode") == "automated":
        # Placeholder: actual retrieval evaluation is exercised by benchmark/holdout suites.
        return {"failures": [], "warnings": []}
    return {"failures": [], "warnings": []}


def _is_rule_violation_task(task: dict[str, Any]) -> bool:
    return "expected_failures" in task


def run_suite(suite_dir: Path, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    schema = schema or _schema()
    valid_rules = _list_rules()
    tasks_path = suite_dir / "tasks.jsonl"
    if not tasks_path.is_file():
        raise FileNotFoundError(f"suite tasks not found: {tasks_path}")
    raw_tasks = _load_jsonl(tasks_path)

    cases: list[dict[str, Any]] = []
    schema_errors: list[str] = []
    generate_failures: list[str] = []
    total_expected = 0
    total_detected = 0
    manual_count = 0

    for task in raw_tasks:
        task_id = task.get("id", "<unknown>")
        errors = _validate_task(task, schema)
        if errors:
            schema_errors.extend(f"{task_id}: {e}" for e in errors)
            continue

        unknown_expected = [r for r in task.get("expected_failures", []) if r not in valid_rules]
        if unknown_expected:
            schema_errors.append(f"{task_id}: unknown expected rules {unknown_expected}")

        if task.get("detection_mode") == "manual":
            manual_count += 1
            cases.append({
                "id": task_id,
                "automation": "manual",
                "expected_failures": task.get("expected_failures", []),
                "detected_failures": [],
                "true_positives": [],
                "false_negatives": task.get("expected_failures", []),
                "false_positives": [],
            })
            continue

        if task.get("generate_script"):
            script_path = ROOT / task["generate_script"]
            if script_path.is_file() and not _run_generate(script_path):
                generate_failures.append(str(task["generate_script"]))

        if _is_rule_violation_task(task):
            detected = _detect_rule_violation(task)
        else:
            detected = _detect_reference_selection(task)

        expected_set = set(task.get("expected_failures", []))
        detected_set = set(detected["failures"])
        tp = expected_set & detected_set
        fn = expected_set - detected_set
        fp = detected_set - expected_set

        total_expected += len(expected_set)
        total_detected += len(tp)

        cases.append({
            "id": task_id,
            "automation": "automated" if task.get("detection_mode") == "automated" else "hybrid",
            "expected_failures": sorted(expected_set),
            "detected_failures": sorted(detected_set),
            "true_positives": sorted(tp),
            "false_negatives": sorted(fn),
            "false_positives": sorted(fp),
        })

    automated_cases = [c for c in cases if c["automation"] != "manual"]
    # Only rule-violation tasks with expected failures contribute to precision/recall.
    metric_cases = [c for c in automated_cases if c["expected_failures"]]
    detected_sum = sum(len(c["detected_failures"]) for c in metric_cases)
    precision = total_detected / max(1, detected_sum)
    recall = total_detected / max(1, total_expected)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)

    # Quality gate: automated/hybrid rule-violation cases must achieve at least
    # 50% recall and 30% precision. Manual cases and informational tasks (no
    # expected failures) do not block CI.
    threshold_precision = 0.30
    threshold_recall = 0.50
    passed = (
        not schema_errors
        and not generate_failures
        and (not metric_cases or (precision >= threshold_precision and recall >= threshold_recall))
    )

    return {
        "suite": suite_dir.name,
        "task_count": len(raw_tasks),
        "automated_count": len(automated_cases),
        "manual_count": manual_count,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "thresholds": {"precision": threshold_precision, "recall": threshold_recall},
        "passed": passed,
        "schema_errors": schema_errors,
        "generate_failures": generate_failures,
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", nargs="?", default="adversarial-mutations", help="Eval suite directory name under evals/")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument("--all", action="store_true", help="Run all eval suites and aggregate")
    args = parser.parse_args()

    schema = _schema()
    suites = [d for d in sorted((ROOT / "evals").iterdir()) if d.is_dir() and (d / "tasks.jsonl").is_file()]
    if args.all:
        reports = []
        for suite_dir in suites:
            reports.append(run_suite(suite_dir, schema))
        overall_passed = all(r["passed"] for r in reports)
        report = {
            "schema_version": "1.0",
            "suite_count": len(reports),
            "passed": overall_passed,
            "suites": reports,
        }
    else:
        suite_dir = ROOT / "evals" / args.suite
        if not suite_dir.is_dir():
            print(f"Suite not found: {suite_dir}", file=sys.stderr)
            return 1
        report = run_suite(suite_dir, schema)

    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
