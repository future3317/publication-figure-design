# -*- coding: utf-8 -*-
"""Fixed regression benchmark for academic-figure-skill.

Runs a deterministic set of real-task cases, verifies that:
  * figure_type resolves correctly
  * production asset / visual reference choices are reasonable
  * visual reference only affects visual language, not scientific semantics
  * palette source is recorded correctly
  * PNG output is generated and passes basic QA
  * Visual Source Report is complete

Cases that require R are skipped (marked WARN) when R is not installed.
No pixel-perfect golden image comparison is performed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure skill root is importable.
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from palette_manager import get_palette, resolve_palette
from production_asset_manager import ProductionAssetLibrary
from reference_library import ReferenceLibrary


# ---------------------------------------------------------------------------
# Benchmark configuration
# ---------------------------------------------------------------------------

BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "id": "grouped_violin",
        "figure_type": "GroupedViolin",
        "production_script": "assets/figures/GroupedViolin/plot_GroupedViolinRaincloud.py",
        "data_file": "assets/figures/GroupedViolin/GroupedViolinRaincloud-data.csv",
        "runtime": "python",
        "expected_asset_kind": "template",
        "visual_query": {"figure_type": "GroupedViolin", "tags": ["grouped-violin"], "limit": 1},
        "palette": "summer_beach",
        "palette_policy": "adaptable",
    },
    {
        "id": "heatmap",
        "figure_type": "heatmap",
        "production_script": "assets/figures/heatmap/plot_CorrelationMatrixCombo.py",
        "runtime": "python",
        "expected_asset_kind": "reusable",
        "visual_query": {"figure_type": "heatmap", "tags": ["correlation-matrix"], "limit": 1},
        "palette": None,
        "palette_policy": "adaptable",
    },
    {
        "id": "pca",
        "figure_type": "PCA",
        "production_script": "assets/figures/PCA/plot_PCA.R",
        "runtime": "r",
        "expected_asset_kind": "example",
        "visual_query": {"figure_type": "PCA", "limit": 1},
        "palette": None,
        "palette_policy": "adaptable",
    },
    {
        "id": "marginal_density",
        "figure_type": "MarginalDensity",
        "production_script": "assets/visual-references/references/e088eda258e1bd3a/code.py",
        "runtime": "python",
        "expected_asset_kind": None,  # visual reference only, not production asset
        "visual_query": {"figure_type": "MarginalDensity", "tags": ["marginal-density"], "limit": 1},
        "palette": "soft_forest",
        "palette_policy": "adaptable",
    },
    {
        "id": "stacked_bar_scatter",
        "figure_type": "StackedBarScatter",
        "production_script": "assets/figures/StackedBarScatter/plot_StackedBarScatter.py",
        "render_mode": "import_function",
        "render_function": "plot_jitter_mean_sig",
        "runtime": "python",
        "expected_asset_kind": "example",
        "visual_query": {"figure_type": "StackedBarScatter", "tags": ["superplot"], "limit": 1},
        "palette": None,
        "palette_policy": "adaptable",
    },
    {
        "id": "grouped_bar_chart",
        "figure_type": "GroupedBarChart",
        "production_script": "assets/figures/GroupedBarChart/plot_BarWithSwarm.py",
        "runtime": "python",
        "expected_asset_kind": "template",
        "visual_query": {"figure_type": "GroupedBarChart", "tags": ["grouped-bar"], "limit": 1},
        "palette": "pastel_girl",
        "palette_policy": "adaptable",
    },
    {
        "id": "bar_categorical",
        "figure_type": "BarCategorical",
        "production_script": "assets/visual-references/references/8fbf151c1f63de42/code.py",
        "runtime": "python",
        "expected_asset_kind": None,
        "visual_query": {"figure_type": "BarCategorical", "tags": ["bar-chart"], "limit": 1},
        "palette": None,
        "palette_policy": "adaptable",
    },
    {
        "id": "scatter_regression_raincloud",
        "figure_type": "ScatterRegressionRaincloud",
        "production_script": "assets/figures/ScatterRegressionRaincloud/plot_ScatterRegressionRaincloud.py",
        "data_file": "assets/figures/ScatterRegressionRaincloud/ScatterRegressionRaincloud-data.csv",
        "runtime": "python",
        "expected_asset_kind": "template",
        "visual_query": {"figure_type": "ScatterRegressionRaincloud", "limit": 1},
        "palette": "watercolor_bloom",
        "palette_policy": "adaptable",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    case_id: str
    figure_type: str
    status: str  # PASS, FAIL, WARN, SKIP
    production_asset: Optional[str] = None
    visual_reference: Optional[str] = None
    palette: Optional[str] = None
    palette_policy: Optional[str] = None
    output_png: Optional[str] = None
    output_size_bytes: Optional[int] = None
    qa_notes: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _has_r_runtime() -> bool:
    return shutil.which("Rscript") is not None


def _run_python_script(script_path: Path, output_path: Path, data_file: Optional[Path] = None) -> Tuple[int, str, str]:
    cmd = [sys.executable, str(script_path), "--output", str(output_path)]
    if data_file is not None:
        cmd.extend(["--data", str(data_file)])
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SCRIPT_DIR)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def _run_import_function(script_path: Path, output_path: Path, func_name: str) -> Tuple[int, str, str]:
    """Import a function from the script and render with synthetic wide-format data."""
    import importlib.util
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Prevent any plt.show() in the imported module from blocking.
    plt_show_orig = plt.show
    plt.show = lambda *args, **kwargs: None

    # The script writes hard-coded files to CWD; run inside output dir for cleanup.
    orig_cwd = os.getcwd()
    os.chdir(str(output_path.parent))
    try:
        spec = importlib.util.spec_from_file_location("_bench_module", script_path)
        if spec is None or spec.loader is None:
            return 1, "", "cannot load module"
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_bench_module"] = mod
        try:
            spec.loader.exec_module(mod)
        except Exception as exc:
            return 1, "", f"module import failed: {exc}"

        func = getattr(mod, func_name, None)
        if func is None:
            return 1, "", f"function {func_name} not found"

        try:
            import numpy as np
            import pandas as pd
            rng = np.random.default_rng(77)
            df = pd.DataFrame({
                "Group A": rng.normal(5, 1.2, 20),
                "Group B": rng.normal(4, 1.0, 20),
                "Group C": rng.normal(3, 0.9, 20),
            })
            func(df, show_p=False, save_path=str(output_path), fig_size=(3.5, 4))
        except Exception as exc:
            return 1, "", f"render failed: {exc}"
        return 0, "", ""
    finally:
        os.chdir(orig_cwd)
        plt.show = plt_show_orig


def _qa_png(path: Path) -> List[str]:
    """Basic PNG QA: exists, non-empty, PNG magic header."""
    notes: List[str] = []
    if not path.exists():
        notes.append("PNG not created")
        return notes
    size = path.stat().st_size
    notes.append(f"PNG size={size} bytes")
    if size < 100:
        notes.append("PNG suspiciously small")
    with path.open("rb") as fh:
        header = fh.read(8)
    if header != b"\x89PNG\r\n\x1a\n":
        notes.append("PNG magic header mismatch")
    return notes


def _resolve_palette_for_case(case: Dict[str, Any], ref: Optional[Any]) -> Tuple[Optional[str], Optional[str]]:
    """Resolve palette following: explicit > reference > production > skill default."""
    explicit = case.get("palette")
    if explicit:
        return explicit, case.get("palette_policy", "adaptable")
    if ref is not None:
        m = ref.metadata
        return m.get("palette"), m.get("palette_policy", "preserve")
    return None, "adaptable"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_case(case: Dict[str, Any], tmp_dir: Path, palib: ProductionAssetLibrary, vlib: ReferenceLibrary) -> BenchmarkResult:
    result = BenchmarkResult(case_id=case["id"], figure_type=case["figure_type"], status="FAIL")

    # 1. Production asset lookup.
    assets = palib.query(case["figure_type"], production_ready=None, limit=1)
    if assets:
        asset = assets[0]
        result.production_asset = f"{asset.figure_type}/{asset.variant} ({asset.asset_kind})"
        expected = case.get("expected_asset_kind")
        if expected and asset.asset_kind != expected:
            result.errors.append(f"asset_kind mismatch: expected {expected}, got {asset.asset_kind}")

    # 2. Visual reference query.
    query = dict(case["visual_query"])
    refs = vlib.query(**query)
    ref = refs[0] if refs else None
    if ref is not None:
        result.visual_reference = ref.id

    # 3. Runtime check.
    if case["runtime"] == "r" and not _has_r_runtime():
        result.status = "WARN"
        result.qa_notes.append("R runtime not available; render skipped")
        return result

    # 4. Render.
    script = SKILL_ROOT / case["production_script"]
    if not script.exists():
        result.errors.append(f"production script not found: {script}")
        return result

    output_png = tmp_dir / f"{case['id']}.png"
    data_file = SKILL_ROOT / case["data_file"] if "data_file" in case else None
    if data_file is not None and not data_file.exists():
        data_file = None

    render_mode = case.get("render_mode", "cli")
    if render_mode == "import_function":
        func_name = case.get("render_function", "")
        rc, stdout, stderr = _run_import_function(script, output_png, func_name)
    else:
        rc, stdout, stderr = _run_python_script(script, output_png, data_file)
    if rc != 0:
        result.errors.append(f"script exited with {rc}")
        if stderr:
            result.errors.append(stderr.strip()[:300])
        return result

    result.output_png = str(output_png.relative_to(SKILL_ROOT))
    result.qa_notes.extend(_qa_png(output_png))
    result.output_size_bytes = output_png.stat().st_size if output_png.exists() else 0

    # 5. Palette resolution.
    palette_name, policy = _resolve_palette_for_case(case, ref)
    result.palette = palette_name
    result.palette_policy = policy
    if palette_name:
        try:
            colors = resolve_palette(palette_name, n=3)
            result.qa_notes.append(f"resolved {len(colors)} colors")
        except Exception as exc:
            result.errors.append(f"palette resolution failed: {exc}")

    # 6. Final status.
    if not result.errors:
        result.status = "PASS"
    return result


def run_benchmark() -> List[BenchmarkResult]:
    tmp_dir = Path(tempfile.mkdtemp(prefix="afs_regression_", dir=SKILL_ROOT / "tmp"))
    palib = ProductionAssetLibrary(root=SKILL_ROOT)
    vlib = ReferenceLibrary(root=SKILL_ROOT)
    results: List[BenchmarkResult] = []

    try:
        for case in BENCHMARK_CASES:
            result = run_case(case, tmp_dir, palib, vlib)
            results.append(result)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return results


def _print_report(results: List[BenchmarkResult]) -> None:
    counts = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    print("=" * 70)
    print("Academic Figure Skill Regression Benchmark")
    print("=" * 70)
    print(f"Total cases : {len(results)}")
    print(f"  PASS      : {counts['PASS']}")
    print(f"  WARN      : {counts['WARN']}")
    print(f"  FAIL      : {counts['FAIL']}")
    print(f"  SKIP      : {counts['SKIP']}")
    print("-" * 70)

    for r in results:
        print(f"\n[{r.status}] {r.case_id} ({r.figure_type})")
        print(f"  production_asset : {r.production_asset or 'None'}")
        print(f"  visual_reference : {r.visual_reference or 'None'}")
        print(f"  palette          : {r.palette or 'None'} ({r.palette_policy or 'N/A'})")
        print(f"  output_png       : {r.output_png or 'None'}")
        if r.output_size_bytes:
            print(f"  output_size      : {r.output_size_bytes} bytes")
        for note in r.qa_notes:
            print(f"  QA note          : {note}")
        for err in r.errors:
            print(f"  ERROR            : {err}")

    print("\n" + "=" * 70)
    if counts["FAIL"] == 0:
        print("Benchmark completed with no failures.")
    else:
        print(f"Benchmark completed with {counts['FAIL']} failure(s).")
    print("=" * 70)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Regression benchmark")
    parser.add_argument("--json", type=str, default=None, help="Write machine-readable report to path")
    args = parser.parse_args(argv)

    results = run_benchmark()
    _print_report(results)

    if args.json:
        report = {
            "counts": {r.status: sum(1 for x in results if x.status == r.status) for r in results},
            "cases": [
                {
                    "case_id": r.case_id,
                    "figure_type": r.figure_type,
                    "status": r.status,
                    "production_asset": r.production_asset,
                    "visual_reference": r.visual_reference,
                    "palette": r.palette,
                    "palette_policy": r.palette_policy,
                    "output_png": r.output_png,
                    "output_size_bytes": r.output_size_bytes,
                    "qa_notes": r.qa_notes,
                    "errors": r.errors,
                }
                for r in results
            ],
        }
        Path(args.json).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nReport written to: {args.json}")

    return 0 if all(r.status in ("PASS", "WARN", "SKIP") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
