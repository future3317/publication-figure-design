#!/usr/bin/env python3
"""Freeze the current real-paper sprint as the visual regression baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "tmp" / "visual_sprint" / "sprint_report.json"
DEFAULT_OUTPUT = ROOT / "assets" / "reference-benchmarks" / "visual-baseline-v1.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze(report_path: Path, output_path: Path, *, replace: bool = False) -> dict:
    report_path = report_path.resolve()
    output_path = output_path.resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    tasks = list(report.get("tasks", []))
    if len(tasks) != 25:
        raise ValueError(f"expected 25 sprint tasks, found {len(tasks)}")
    baseline_id = output_path.stem
    if not baseline_id.startswith("visual-baseline-"):
        raise ValueError("output filename must use the visual-baseline-<name>.json form")
    baseline_dir = output_path.with_suffix("")
    if not replace and (output_path.exists() or baseline_dir.exists()):
        raise FileExistsError(f"baseline already exists: {output_path}; pass --replace only to intentionally replace it")
    if baseline_dir.exists():
        shutil.rmtree(baseline_dir)
    baseline_dir.mkdir(parents=True, exist_ok=True)
    frozen = []
    reason_counts = Counter()
    for row in tasks:
        family = str(row["figure_family"])
        task_id = str(row["id"])
        source = Path(str(row["candidate_paths"][f"{family}__balanced"]))
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = baseline_dir / f"{task_id}.png"
        shutil.copy2(source, destination)
        qa = row.get("qa", {}).get(f"{family}__balanced", {})
        for pair in row.get("pairwise", []):
            reason_counts.update(pair.get("consensus", {}).get("reason_codes", []))
        frozen.append({
            "task_id": task_id,
            "figure_family": family,
            "source_image": row.get("source_image", ""),
            "image": str(destination.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256(destination),
            "L0": bool((qa.get("L0") or {}).get("passed")),
            "L1": bool((qa.get("L1") or {}).get("passed")),
        })
    payload = {
        "schema_version": "1.0",
        "baseline_id": baseline_id,
        "source_report": str(report_path.relative_to(ROOT)).replace("\\", "/"),
        "source_render_variant": True,
        "candidate_strategy": "balanced",
        "renderer_version": "sprint-1",
        "task_count": len(frozen),
        "reason_code_counts": dict(sorted(reason_counts.items())),
        "tasks": frozen,
        "promotion_policy": "new real renders must beat this baseline by blind swapped review; source_render_variant never promotes a Champion",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--replace", action="store_true", help="replace an existing baseline explicitly")
    args = parser.parse_args()
    payload = freeze(args.report, args.output, replace=args.replace)
    print(json.dumps({"baseline_id": payload["baseline_id"], "task_count": payload["task_count"], "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
