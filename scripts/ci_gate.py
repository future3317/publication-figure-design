#!/usr/bin/env python3
"""Single mandatory CI gate for the publication-figure-design skill."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT / "scripts")}


def run_step(name: str, args: list[str]) -> None:
    print(f"\n=== {name} ===", flush=True)
    completed = subprocess.run([PYTHON, *args], cwd=ROOT, env=ENV)
    if completed.returncode:
        raise SystemExit(f"CI gate failed at {name} (exit {completed.returncode})")


def main() -> int:
    run_step("contract", ["scripts/check_skill_contract.py"])
    run_step("unit", ["-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py", "-q"])
    run_step("package", ["-m", "unittest", "discover", "-s", "src/publication_figure_design/tests", "-p", "test_*.py", "-q"])
    run_step("reference validate", ["scripts/reference_library.py", "validate"])
    run_step("reference DNA", ["scripts/check_reference_dna.py"])
    run_step("reference reconstruction", ["scripts/check_reference_reproductions.py"])
    run_step("reference fidelity", ["scripts/check_reference_reproduction_fidelity.py"])
    run_step("source reconstruction", ["scripts/check_source_reconstruction_library.py"])
    run_step("source catalog", ["scripts/check_source_reference_catalog.py"])
    run_step("benchmark", ["scripts/evaluate_benchmark.py", "--enforce"])
    run_step("holdout", ["scripts/evaluate_holdout.py", "--enforce"])
    run_step("adversarial retrieval", ["scripts/adversarial_retrieval.py"])
    run_step("scale benchmark", ["scripts/scale_benchmark.py"])
    run_step("generation corpus", ["scripts/evaluate_generation_regression.py", "--contract-only", "--enforce"])
    run_step("champion floors", ["scripts/check_champion_floors.py"])
    run_step("quarantine", ["scripts/check_reference_quarantine.py"])
    run_step("activation eval", ["scripts/evaluate_activation.py", "evals/activation/validation.jsonl"])
    run_step("adapter generation", ["scripts/generate_adapters.py"])
    run_step("adapter canary", ["scripts/adapter_canary.py"])
    with tempfile.TemporaryDirectory(prefix="pfd-ci-") as temp:
        session = Path(temp) / "session.json"
        run_step("pfd lifecycle canary", ["-m", "publication_figure_design.cli", "run", "tests/fixtures/task_spec_canary.json", "--output", str(session)])
    print("\nALL CI GATES PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
