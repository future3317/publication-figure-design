#!/usr/bin/env python3
"""Build and validate the Figure Family Champion Board.

The board is a small evidence ledger. This command joins it with the current
reference registry, generation-regression corpus, pairwise preference records, and
blind-judge calibration evidence to report where visual quality is actually supported.
An unseeded family is reported as ``needs_evidence``; it is not silently promoted
from a high metadata score.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

try:
    from figure_family_coverage import FIGURE_FAMILIES
except ImportError:  # pragma: no cover - package import fallback
    from scripts.figure_family_coverage import FIGURE_FAMILIES


BOARD_PATH = Path("assets/reference-benchmarks/champion_board.json")
CORPUS_PATH = Path("assets/reference-benchmarks/generation_regression_corpus.json")
REAL_TASK_PATH = Path("assets/reference-benchmarks/real_generation_tasks.json")
PREFERENCE_PATH = Path("assets/reference-benchmarks/preference_pairs.jsonl")
REASON_CODES = {
    "layout",
    "hierarchy",
    "spacing",
    "typography",
    "palette",
    "annotation",
    "data_clarity",
    "overall_polish",
}
REASON_ALIASES = {
    "whitespace": "spacing",
    "professional_finish": "overall_polish",
    "palette_discipline": "palette",
    "annotation_clearance": "annotation",
}


def _norm(value: Any) -> str:
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value or ""))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number}: preference row must be an object")
        rows.append(row)
    return rows


def _registry(root: Path) -> list[dict[str, Any]]:
    path = root / "assets" / "registry.jsonl"
    return _read_jsonl(path)


def _eligible(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("review_status") in {"reviewed", "promoted"}
        and record.get("lifecycle_state", "benchmarked") in {"benchmarked", "production"}
    ]


def _field_values(records: Iterable[dict[str, Any]], field: str) -> set[str]:
    return {str(record.get(field)).strip() for record in records if str(record.get(field) or "").strip()}


def _palette_signature(record: dict[str, Any]) -> str:
    grammar = record.get("visual_grammar") or {}
    roles = grammar.get("palette_roles") or {}
    if isinstance(roles, dict):
        return "|".join(sorted(str(key) for key in roles)) or str(record.get("palette_policy") or "unknown")
    return str(record.get("palette_policy") or "unknown")


def _review_pass(record: dict[str, Any]) -> bool:
    review = record.get("visual_review") or {}
    if not isinstance(review, dict):
        return False
    return all(review.get(key) in {"pass", "justified_deviation"} for key in ("hierarchy", "panel_balance", "text_legibility", "whitespace"))


def _grammar_presence(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for record in records:
        grammar = record.get("visual_grammar") or {}
        annotations = grammar.get("annotations_typography") or {}
        composition = grammar.get("canvas_composition") or {}
        repetition = grammar.get("repetition_structures") or {}
        tags = {_norm(tag) for tag in record.get("tags", [])}
        if annotations or {"direct_label", "direct_labels", "legendless"} & tags:
            counts["annotation_grammar"] += 1
        if composition or repetition:
            counts["multi_panel_topology"] += 1
        density = record.get("data_density") or (record.get("observable_visual_grammar") or {}).get("density")
        if density in {"dense", "high"}:
            counts["dense"] += 1
        if density in {"sparse", "low", "focused"}:
            counts["sparse"] += 1
        if record.get("journal_style"):
            counts["journal_profile"] += 1
        if record.get("palette") or record.get("palette_policy") or (grammar.get("palette_roles") or {}):
            counts["palette_roles"] += 1
        if {"direct_label", "direct_labels", "legendless"} & tags or "direct_label" in str(annotations).lower():
            counts["direct_label_or_legendless"] += 1
        layout = _norm(record.get("layout"))
        if "asym" in layout or (record.get("observable_visual_grammar") or {}).get("hero_panel"):
            counts["asymmetric_hero"] += 1
        figure_type = _norm(record.get("figure_type"))
        if figure_type in {"spatial_image_plate", "single_cell_systems", "in_vivo_efficacy", "mixed_multi_panel"}:
            counts["mixed_image_quantitative"] += 1
    return dict(counts)


def _family_records(records: list[dict[str, Any]], figure_types: list[str]) -> list[dict[str, Any]]:
    wanted = {_norm(value) for value in figure_types}
    return [record for record in _eligible(records) if _norm(record.get("figure_type")) in wanted]


def _family_tasks(corpus: dict[str, Any], family_id: str, figure_types: list[str]) -> list[dict[str, Any]]:
    wanted = {_norm(value) for value in figure_types}
    tasks = []
    for task in corpus.get("tasks", []):
        task_family = _norm(task.get("figure_family"))
        task_id = _norm(task.get("id"))
        if task_family == _norm(family_id) or task_family in wanted or task_id in wanted:
            tasks.append(task)
    return tasks


def _generation_tasks(root: Path, corpus: dict[str, Any]) -> list[dict[str, Any]]:
    """Join the fixed regression identities with executed real-paper tasks.

    The regression corpus remains the release gate.  The real-paper manifest is
    separate evidence for the frozen visual sprint and is only joined here so the
    Champion Board reports actual task coverage instead of counting placeholders.
    """
    tasks = list(corpus.get("tasks", []))
    manifest_path = root / REAL_TASK_PATH
    if not manifest_path.is_file():
        return tasks
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing = {str(task.get("id")) for task in tasks}
    for task in payload.get("tasks", []):
        if str(task.get("id")) not in existing:
            tasks.append(task)
    return tasks


def _preference_ids(row: dict[str, Any]) -> tuple[str, str]:
    preferred = str(row.get("preferred") or row.get("winner") or "")
    rejected = str(row.get("rejected") or "")
    if not rejected:
        left, right = str(row.get("left_id") or ""), str(row.get("right_id") or "")
        rejected = right if preferred == left else left
    return preferred, rejected


def _reason_codes(row: dict[str, Any]) -> list[str]:
    values = row.get("reason_codes") or row.get("reasons") or []
    return [REASON_ALIASES.get(str(value).strip(), str(value).strip()) for value in values if str(value).strip()]


def _validate_board(board: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if board.get("schema_version") != "1.0":
        failures.append("champion board schema_version must be 1.0")
    policy = board.get("policy") or {}
    if int(policy.get("target_task_min", 0)) != 5 or int(policy.get("target_task_max", 0)) != 20:
        failures.append("champion board target task range must be 5..20")
    focus = board.get("focus")
    if not isinstance(focus, dict):
        failures.append("champion board focus must be an object")
    else:
        active = focus.get("active_families")
        if not isinstance(active, list) or len(active) != 5 or len(set(active)) != 5:
            failures.append("champion board focus must declare exactly five unique families")
        if int(focus.get("task_target", 0)) != 5:
            failures.append("champion board focus task_target must be 5")
        if int(focus.get("max_candidates", 0)) != 3:
            failures.append("champion board focus max_candidates must be 3")
        if int(focus.get("max_repairs", 0)) != 1:
            failures.append("champion board focus max_repairs must be 1")
        if int(focus.get("max_judge_rounds", 0)) != 2:
            failures.append("champion board focus max_judge_rounds must be 2")
        if set(focus.get("reason_codes", [])) != REASON_CODES:
            failures.append("champion board focus reason_codes must be the canonical eight codes")
        ready_rule = focus.get("ready_rule")
        expected_rule = {
            "generation_tasks": 5,
            "preference_pairs": 5,
            "auto_pairwise_count": 10,
            "judge_order_consistency": 0.9,
            "degradation_detection_rate": 0.9,
            "challenger_win_rate": 0.6,
            "scientific_pass": True,
            "L0": True,
            "L1": True,
            "champion": True,
            "auto_ready": True,
        }
        if ready_rule != expected_rule:
            failures.append("champion board focus ready_rule does not match the evidence policy")
    families = board.get("families")
    if not isinstance(families, dict):
        return failures + ["champion board families must be an object"]
    missing = sorted(set(FIGURE_FAMILIES) - set(families))
    if missing:
        failures.append("board missing figure families: " + ", ".join(missing))
    active = set((board.get("focus") or {}).get("active_families", []))
    unknown_focus = sorted(active - set(families))
    if unknown_focus:
        failures.append("focus family is not present in board: " + ", ".join(unknown_focus))
    for family_id, row in families.items():
        if not isinstance(row, dict):
            failures.append(f"{family_id}: board row must be an object")
            continue
        for key in ("champion", "challenger", "last_release", "evidence", "status"):
            if key not in row:
                failures.append(f"{family_id}: missing {key}")
        if row.get("status") not in {"needs_evidence", "ready", "blocked"}:
            failures.append(f"{family_id}: invalid status {row.get('status')!r}")
    return failures


def build_report(root: Path, board: dict[str, Any]) -> dict[str, Any]:
    records = _registry(root)
    corpus_path = root / CORPUS_PATH
    corpus = json.loads(corpus_path.read_text(encoding="utf-8")) if corpus_path.is_file() else {"tasks": []}
    generation_tasks = _generation_tasks(root, corpus)
    preferences = _read_jsonl(root / PREFERENCE_PATH)
    preference_families = {family: [row for row in preferences if _norm(row.get("figure_family")) == _norm(family)] for family in FIGURE_FAMILIES}
    assigned_preference_count = sum(len(rows) for rows in preference_families.values())
    rows: list[dict[str, Any]] = []
    for family_id, spec in FIGURE_FAMILIES.items():
        family_records = _family_records(records, list(spec["figure_types"]))
        tasks = _family_tasks({"tasks": generation_tasks}, family_id, list(spec["figure_types"]))
        ratings = [float(record["aesthetic_rating"]) / 5.0 for record in family_records if isinstance(record.get("aesthetic_rating"), (int, float))]
        review_pass_rate = mean([1.0 if _review_pass(record) else 0.0 for record in family_records]) if family_records else 0.0
        quality = round(mean([mean(ratings), review_pass_rate]) if ratings else review_pass_rate, 4)
        type_counts = {_norm(figure_type): sum(1 for record in family_records if _norm(record.get("figure_type")) == _norm(figure_type)) for figure_type in spec["figure_types"]}
        covered_types = sum(value > 0 for value in type_counts.values())
        type_coverage = covered_types / len(type_counts) if type_counts else 0.0
        values = {
            "subtypes": _field_values(family_records, "subtype"),
            "layouts": _field_values(family_records, "layout"),
            "palettes": {_palette_signature(record) for record in family_records},
            "journals": _field_values(family_records, "journal_style"),
            "densities": {str(record.get("data_density") or (record.get("observable_visual_grammar") or {}).get("density")) for record in family_records if record.get("data_density") or (record.get("observable_visual_grammar") or {}).get("density")},
        }
        diversity_parts = {
            "subtype": min(1.0, len(values["subtypes"]) / 3.0),
            "layout": min(1.0, len(values["layouts"]) / 3.0),
            "palette": min(1.0, len(values["palettes"]) / 3.0),
            "journal": min(1.0, len(values["journals"]) / 2.0),
            "density": min(1.0, len(values["densities"]) / 2.0),
        }
        diversity = round(mean(diversity_parts.values()), 4)
        preference_rows = preference_families[family_id]
        board_row = board["families"][family_id]
        preferred = [(_preference_ids(row)[0]) for row in preference_rows]
        champion_id = str(board_row.get("champion") or "")
        win_rate = (sum(value == champion_id for value in preferred) / len(preferred)) if champion_id and preferred else None
        grammar = _grammar_presence(family_records)
        gaps = [name for name in ("annotation_grammar", "multi_panel_topology", "dense", "sparse", "journal_profile", "palette_roles", "direct_label_or_legendless", "asymmetric_hero", "mixed_image_quantitative") if grammar.get(name, 0) == 0]
        evidence = board_row.get("evidence") or {}
        focus = board.get("focus", {})
        active_families = set(focus.get("active_families", []))
        is_focus = family_id in active_families
        ready_rule = focus.get("ready_rule", {}) if is_focus else {}
        readiness = board_row.get("status")
        if is_focus:
            candidate_contract_pass = all(
                isinstance(row.get("candidate_ids"), list)
                and len(row.get("candidate_ids", [])) == int(focus.get("max_candidates", 3))
                for row in preference_rows
            )
            evidence_pass = (
                float(evidence.get("auto_pairwise_count", 0)) >= int(ready_rule.get("auto_pairwise_count", 10))
                and float(evidence.get("judge_order_consistency", 0.0)) >= float(ready_rule.get("judge_order_consistency", 0.9))
                and float(evidence.get("degradation_detection_rate", 0.0)) >= float(ready_rule.get("degradation_detection_rate", 0.9))
                and float(evidence.get("challenger_win_rate", 0.0)) >= float(ready_rule.get("challenger_win_rate", 0.6))
            )
            ready = (
                len(tasks) >= int(ready_rule.get("generation_tasks", 5))
                and len(preference_rows) >= int(ready_rule.get("preference_pairs", 5))
                and candidate_contract_pass
                and evidence_pass
                and (not ready_rule.get("scientific_pass") or evidence.get("scientific_pass") is True)
                and (not ready_rule.get("L0") or evidence.get("L0") is True)
                and (not ready_rule.get("L1") or evidence.get("L1") is True)
                and (not ready_rule.get("champion") or bool(board_row.get("champion")))
                and (not ready_rule.get("auto_ready") or evidence.get("auto_ready") is True)
            )
            readiness = "ready" if ready else "needs_evidence"
        elif readiness == "ready" and (len(tasks) < 5 or not board_row.get("champion") or evidence.get("scientific_pass") is not True):
            readiness = "needs_evidence"
        rows.append({
            "id": family_id,
            "focus": is_focus,
            "figure_types": list(spec["figure_types"]),
            "reference_count": len(family_records),
            "task_count": len(tasks),
            "target_task_range": [5, 20],
            "type_coverage": round(type_coverage, 4),
            "quality_score": quality,
            "quality_components": {"aesthetic": round(mean(ratings), 4) if ratings else 0.0, "visual_review_pass_rate": round(review_pass_rate, 4)},
            "diversity_score": diversity,
            "diversity_components": diversity_parts,
            "coverage_quality_diversity": round(type_coverage * quality * diversity, 4),
            "observed_grammar_counts": grammar,
            "gaps": gaps,
            "champion": champion_id or None,
            "challenger": board_row.get("challenger"),
            "last_release": board_row.get("last_release"),
            "human_preference_win_rate": round(win_rate, 4) if win_rate is not None else None,
            "preference_pair_count": len(preference_rows),
            "candidate_contract_pass": all(
                isinstance(row.get("candidate_ids"), list)
                and len(row.get("candidate_ids", [])) == int(focus.get("max_candidates", 3))
                for row in preference_rows
            ) if is_focus else None,
            "reason_codes": sorted({code for row in preference_rows for code in _reason_codes(row)}),
            "scientific_pass": evidence.get("scientific_pass"),
            "L0": evidence.get("L0"),
            "L1": evidence.get("L1"),
            "L2": evidence.get("L2"),
            "L3": evidence.get("L3"),
            "repair_iterations": evidence.get("repair_iterations"),
            "auto_pairwise_count": evidence.get("auto_pairwise_count"),
            "judge_order_consistency": evidence.get("judge_order_consistency"),
            "degradation_detection_rate": evidence.get("degradation_detection_rate"),
            "challenger_win_rate": evidence.get("challenger_win_rate"),
            "auto_ready": evidence.get("auto_ready"),
            "status": readiness,
        })
    scores = [row["coverage_quality_diversity"] for row in rows]
    return {
        "schema_version": "1.0",
        "baseline": board.get("baseline", {}),
        "policy": board.get("policy", {}),
        "summary": {
            "family_count": len(rows),
            "ready_family_count": sum(row["status"] == "ready" for row in rows),
            "focus_family_count": len(board.get("focus", {}).get("active_families", [])),
            "focus_ready_family_count": sum(row["status"] == "ready" for row in rows if row["focus"]),
            "mean_coverage_quality_diversity": round(mean(scores), 4) if scores else 0.0,
            "min_coverage_quality_diversity": round(min(scores), 4) if scores else 0.0,
            "preference_pair_count": len(preferences),
            "unassigned_preference_pair_count": len(preferences) - assigned_preference_count,
            "generation_task_count": len(generation_tasks),
        },
        "families": rows,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=root / BOARD_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--enforce", action="store_true", help="fail on malformed board or invalid preference rows")
    parser.add_argument("--summary", action="store_true", help="print only the aggregate summary")
    args = parser.parse_args()
    board = json.loads(args.board.read_text(encoding="utf-8"))
    failures = _validate_board(board)
    for row in _read_jsonl(root / PREFERENCE_PATH):
        preferred, rejected = _preference_ids(row)
        reasons = row.get("reason_codes") or row.get("reasons") or []
        if not preferred or not rejected or preferred == rejected:
            failures.append("preference row must contain distinct preferred and rejected ids")
        if not reasons:
            failures.append("preference row must contain at least one reason code")
        unknown_reasons = sorted({str(value) for value in reasons if REASON_ALIASES.get(str(value), str(value)) not in REASON_CODES})
        if unknown_reasons:
            failures.append("preference row uses unsupported reason codes: " + ", ".join(unknown_reasons))
        candidate_ids = row.get("candidate_ids")
        if candidate_ids is not None:
            if not isinstance(candidate_ids, list) or len(candidate_ids) != 3:
                failures.append("preference row candidate_ids must contain exactly three candidates when present")
            elif str(row.get("left_id")) not in candidate_ids or str(row.get("right_id")) not in candidate_ids:
                failures.append("preference row candidate_ids must include left_id and right_id")
    report = build_report(root, board)
    report["failures"] = failures
    report["passed"] = not failures
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False) if args.summary else text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if args.enforce and failures:
        for failure in failures:
            print(f"CHAMPION BOARD: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
