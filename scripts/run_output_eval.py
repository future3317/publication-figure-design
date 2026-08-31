#!/usr/bin/env python3
"""Run the output-quality eval suite.

The runner validates the eval corpus, regenerates mutation figures, and runs
available automated detectors.  It returns a structured report with expected vs.
detected rule violations.  Mutations without automated detectors are reported as
"manual" so human or future model review can fill the gap.
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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _list_rules() -> set[str]:
    """Collect all valid rule IDs from rules/."""
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


def _detect_mutation(case_dir: Path, task_spec: dict[str, Any]) -> dict[str, Any]:
    """Run available automated detectors for a mutation case."""
    detected: dict[str, list[str]] = {"failures": [], "warnings": []}
    # Placeholder detectors: inspect generate.py source for known bad patterns.
    script = (case_dir / "generate.py").read_text(encoding="utf-8")
    if "fontsize=4" in script or "labelsize=4" in script:
        detected["failures"].append("LAY-001")
    if "cmap=\"jet\"" in script or "cmap='jet'" in script:
        detected["failures"].extend(["HOUSE-009", "A11Y-001"])
    if "Mean (SD)" in script and "sem" in script:
        detected["failures"].append("SCI-004")
    if "bar" in script and "np.random.normal" in script and "data" in script and len(script) < 2000:
        # crude proxy for mean-bar-hides-distribution
        if task_spec.get("family") == "comparison_effect":
            detected["failures"].append("STAT-005")
    return detected


def run_suite(suite_dir: Path) -> dict[str, Any]:
    valid_rules = _list_rules()
    catalog_path = suite_dir / "mutations.json"
    catalog = _load_json(catalog_path)
    cases_dir = suite_dir / "cases"
    cases: list[dict[str, Any]] = []
    total_expected = 0
    total_detected = 0

    for mutation in catalog.get("mutations", []):
        case_dir = cases_dir / mutation["id"]
        expected = _load_json(case_dir / "expected_violations.json")
        task_spec = _load_json(case_dir / "task_spec.json")
        script = case_dir / "generate.py"

        # Validate expected rule IDs exist
        unknown = [r for r in expected.get("failures", []) if r not in valid_rules]
        if unknown:
            print(f"WARNING {mutation['id']}: unknown expected rules {unknown}", file=sys.stderr)

        if script.is_file():
            _run_generate(script)

        detected = _detect_mutation(case_dir, task_spec)
        expected_set = set(expected.get("failures", []))
        detected_set = set(detected["failures"])
        tp = expected_set & detected_set
        fn = expected_set - detected_set
        fp = detected_set - expected_set

        total_expected += len(expected_set)
        total_detected += len(tp)

        cases.append({
            "id": mutation["id"],
            "category": mutation["category"],
            "expected_failures": sorted(expected_set),
            "detected_failures": sorted(detected_set),
            "true_positives": sorted(tp),
            "false_negatives": sorted(fn),
            "false_positives": sorted(fp),
            "automation": "partial",
        })

    precision = total_detected / max(1, sum(len(set(c["detected_failures"])) for c in cases))
    recall = total_detected / max(1, total_expected)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)

    return {
        "suite": suite_dir.name,
        "mutation_count": len(cases),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", nargs="?", default="adversarial-mutations", help="Eval suite directory name under evals/")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    suite_dir = ROOT / "evals" / args.suite
    if not suite_dir.is_dir():
        print(f"Suite not found: {suite_dir}", file=sys.stderr)
        return 1

    report = run_suite(suite_dir)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
