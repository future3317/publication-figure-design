#!/usr/bin/env python3
"""Compare a new 25-task render against the frozen visual baseline.

Exact matches are reported as unchanged and need no model decision.  Any changed
render must carry forward/reverse blind-judge JSON; missing or inconsistent review
is an uncertain result and blocks promotion.  This script never updates the
Champion Board or treats source-render variants as production champions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from auto_visual_judge import judge_pair
except ImportError:  # pragma: no cover
    from scripts.auto_visual_judge import judge_pair


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "assets" / "reference-benchmarks" / "visual-baseline-v1.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected an object")
    return payload


def _judge_rows(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.is_file():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        task_id = str(row.get("task_id", ""))
        if not task_id:
            raise ValueError(f"{path}:{line_number}: missing task_id")
        rows[task_id] = row
    return rows


def validate_baseline(payload: dict[str, Any], root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    baseline_id = str(payload.get("baseline_id", ""))
    if not re.fullmatch(r"visual-baseline-[A-Za-z0-9._-]+", baseline_id):
        failures.append("baseline_id must use the visual-baseline-<name> form")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 25:
        failures.append("visual baseline must contain exactly 25 tasks")
        return failures
    ids = [str(row.get("task_id", "")) for row in tasks]
    if len(set(ids)) != len(ids) or any(not value for value in ids):
        failures.append("visual baseline task ids must be unique and non-empty")
    for row in tasks:
        image = root / str(row.get("image", ""))
        if not image.is_file():
            failures.append(f"missing baseline image: {image}")
            continue
        expected = str(row.get("sha256", ""))
        if expected and _sha256(image) != expected:
            failures.append(f"baseline image changed: {row.get('task_id')}")
        if row.get("L0") is not True or row.get("L1") is not True:
            failures.append(f"baseline QA is not L0/L1 clean: {row.get('task_id')}")
    return failures


def compare(baseline: dict[str, Any], current: dict[str, Any], judges: dict[str, dict[str, Any]], root: Path = ROOT) -> dict[str, Any]:
    failures = validate_baseline(baseline, root)
    current_rows = {str(row.get("id")): row for row in current.get("tasks", [])}
    results: list[dict[str, Any]] = []
    reason_counts = Counter()
    current_pair_reason_counts = Counter()
    for task_row in current.get("tasks", []):
        for pair in task_row.get("pairwise", []):
            current_pair_reason_counts.update(pair.get("consensus", {}).get("reason_codes", []))
    baseline_reason_counts = Counter(baseline.get("reason_code_counts", {}))
    for base in baseline.get("tasks", []):
        task_id = str(base.get("task_id"))
        row = current_rows.get(task_id)
        if row is None:
            failures.append(f"current report missing task: {task_id}")
            continue
        family = str(base.get("figure_family"))
        candidate_id = f"{family}__balanced"
        current_path = Path(str((row.get("candidate_paths") or {}).get(candidate_id, "")))
        if not current_path.is_file():
            failures.append(f"current report missing balanced render: {task_id}")
            continue
        same = _sha256(root / str(base["image"])) == _sha256(current_path)
        qa = (row.get("qa") or {}).get(candidate_id, {})
        hard_pass = bool((qa.get("L0") or {}).get("passed"))
        scientific_pass = bool((qa.get("L1") or {}).get("passed"))
        if not hard_pass or not scientific_pass:
            failures.append(f"hard QA regression: {task_id}")
        result: dict[str, Any] = {"task_id": task_id, "figure_family": family, "changed": not same, "outcome": "unchanged" if same else "uncertain", "L0": hard_pass, "L1": scientific_pass}
        if not same:
            judge = judges.get(task_id)
            if judge is None:
                failures.append(f"missing swapped judge for changed render: {task_id}")
            else:
                try:
                    consensus = judge_pair(judge["forward"], judge["reverse"])
                except (KeyError, TypeError, ValueError) as exc:
                    failures.append(f"invalid swapped judge for {task_id}: {exc}")
                    consensus = {"accepted": False, "preferred": None, "reason_codes": []}
                result["judge"] = consensus
                if consensus.get("accepted") and consensus.get("preferred") == "current":
                    result["outcome"] = "win"
                elif consensus.get("accepted") and consensus.get("preferred") == "baseline":
                    result["outcome"] = "loss"
                else:
                    result["outcome"] = "uncertain"
                    failures.append(f"uncertain swapped judge: {task_id}")
                reason_counts.update(consensus.get("reason_codes", []))
        results.append(result)
    family_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"wins": 0, "losses": 0, "win": 0, "loss": 0, "uncertain": 0, "unchanged": 0})
    for row in results:
        family_stats[row["figure_family"]][row["outcome"]] += 1
    for family, stats in family_stats.items():
        decided = stats["win"] + stats["loss"]
        stats["win_rate"] = round(stats["win"] / decided, 4) if decided else None
        stats.pop("win")
        stats.pop("loss")
    if not reason_counts:
        reason_counts = current_pair_reason_counts
    reason_delta = {key: reason_counts.get(key, 0) - baseline_reason_counts.get(key, 0) for key in sorted(set(reason_counts) | set(baseline_reason_counts))}
    summary = Counter(row["outcome"] for row in results)
    report = {
        "schema_version": "1.0",
        "baseline_id": baseline.get("baseline_id"),
        "task_count": len(results),
        "overall": {key: summary.get(key, 0) for key in ("win", "loss", "uncertain", "unchanged")},
        "family_win_rates": dict(sorted(family_stats.items())),
        "reason_code_delta": reason_delta,
        "hard_qa_regressions": sorted(set(failure for failure in failures if failure.startswith("hard QA regression:"))),
        "failures": failures,
    }
    report["passed"] = not failures
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--current-report", type=Path)
    parser.add_argument("--judges", type=Path, help="JSONL with task_id, forward, and reverse judge payloads")
    parser.add_argument("--contract-only", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    baseline = _load(args.baseline)
    if args.contract_only:
        report = {"baseline_id": baseline.get("baseline_id"), "task_count": len(baseline.get("tasks", [])), "failures": validate_baseline(baseline), "passed": not validate_baseline(baseline)}
    else:
        if args.current_report is None:
            parser.error("--current-report is required unless --contract-only is used")
        report = compare(baseline, _load(args.current_report), _judge_rows(args.judges))
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
