#!/usr/bin/env python3
"""Validate blind visual-judge responses without absolute aesthetic scores.

The Codex/Luna runtime supplies two structured responses for the same pair with
the display order swapped. This script maps both local labels back to candidate
ids, accepts only an order-consistent winner, and reports calibration metrics for
known original/degraded pairs. It deliberately does not call a model or service.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


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
LABELS = {"A", "B"}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _response(payload: dict[str, Any]) -> dict[str, Any]:
    response = payload.get("judge", payload)
    if not isinstance(response, dict):
        raise ValueError("judge response must be an object")
    preferred = str(response.get("preferred", "")).strip().upper()
    if preferred not in LABELS:
        raise ValueError("preferred must be A or B")
    confidence = response.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        raise ValueError("confidence must be a number in [0, 1]")
    reasons = [str(value).strip() for value in response.get("reason_codes", []) if str(value).strip()]
    unknown = sorted(set(reasons) - REASON_CODES)
    if unknown:
        raise ValueError("unsupported reason_codes: " + ", ".join(unknown))
    problems = [str(value).strip() for value in response.get("problems", []) if str(value).strip()]
    return {
        "preferred": preferred,
        "confidence": round(float(confidence), 4),
        "reason_codes": sorted(set(reasons)),
        "problems": problems,
        "repair_needed": bool(response.get("repair_needed", False)),
    }


def _display_order(payload: dict[str, Any], fallback: list[str]) -> list[str]:
    order = payload.get("display_order", fallback)
    if not isinstance(order, list) or len(order) != 2 or len(set(str(item) for item in order)) != 2:
        raise ValueError("display_order must contain two distinct candidate ids")
    return [str(item) for item in order]


def _canonical_winner(response: dict[str, Any], order: list[str]) -> str:
    return order[0] if response["preferred"] == "A" else order[1]


def judge_pair(forward_payload: dict[str, Any], reverse_payload: dict[str, Any]) -> dict[str, Any]:
    """Return a consensus record for a forward/reverse blind comparison."""

    forward = _response(forward_payload)
    reverse = _response(reverse_payload)
    forward_order = _display_order(forward_payload, ["candidate_a", "candidate_b"])
    reverse_order = _display_order(reverse_payload, list(reversed(forward_order)))
    forward_winner = _canonical_winner(forward, forward_order)
    reverse_winner = _canonical_winner(reverse, reverse_order)
    consistent = forward_winner == reverse_winner
    return {
        "preferred": forward_winner if consistent else None,
        "rejected": (forward_order[1] if forward_winner == forward_order[0] else forward_order[0]) if consistent else None,
        "accepted": consistent,
        "uncertain": not consistent,
        "confidence": round(min(forward["confidence"], reverse["confidence"]), 4),
        "reason_codes": sorted(set(forward["reason_codes"] + reverse["reason_codes"])),
        "problems": forward["problems"] + [problem for problem in reverse["problems"] if problem not in forward["problems"]],
        "repair_needed": forward["repair_needed"] or reverse["repair_needed"],
        "forward": {"display_order": forward_order, "winner": forward_winner},
        "reverse": {"display_order": reverse_order, "winner": reverse_winner},
    }


def calibrate(rows: Iterable[dict[str, Any]], consistency_floor: float = 0.90) -> dict[str, Any]:
    """Score judge responses for known original/degraded pairs."""

    cases = list(rows)
    checked = 0
    correct = 0
    consistent = 0
    failures: list[str] = []
    for index, row in enumerate(cases, 1):
        try:
            result = judge_pair(row["forward"], row["reverse"])
        except (KeyError, TypeError, ValueError) as exc:
            failures.append(f"case {index}: {exc}")
            continue
        checked += 1
        if result["accepted"]:
            consistent += 1
        if result["accepted"] and result["preferred"] == str(row.get("original_id", "")):
            correct += 1
        elif result["accepted"]:
            failures.append(f"case {index}: judge preferred {result['preferred']!r}, expected original")
    accuracy = correct / checked if checked else 0.0
    order_consistency = consistent / checked if checked else 0.0
    report = {
        "case_count": len(cases),
        "checked_case_count": checked,
        "judge_calibration_accuracy": round(accuracy, 4),
        "degradation_detection_rate": round(accuracy, 4),
        "order_consistency": round(order_consistency, 4),
        "floor": consistency_floor,
        "failures": failures,
    }
    report["passed"] = bool(cases) and not failures and accuracy >= consistency_floor and order_consistency >= consistency_floor
    return report


def degrade_image(source: Path, output: Path, kind: str) -> dict[str, Any]:
    """Create one deterministic, visibly degraded calibration image."""

    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
    except ImportError as exc:  # pragma: no cover - environment contract handles this
        raise RuntimeError("Pillow is required for synthetic degradation") from exc
    image = Image.open(source).convert("RGBA")
    width, height = image.size
    if kind == "text_too_small":
        reduced = image.resize((max(1, int(width * 0.72)), max(1, int(height * 0.72))), Image.Resampling.BILINEAR)
        image = reduced.resize((width, height), Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(0.35))
    elif kind == "panel_spacing":
        crop = image.crop((int(width * 0.06), int(height * 0.03), int(width * 0.94), int(height * 0.97)))
        image = crop.resize((width, height), Image.Resampling.BILINEAR)
    elif kind == "palette_contrast":
        image = ImageEnhance.Contrast(image).enhance(0.45)
    elif kind == "panel_alignment":
        shifted = Image.new("RGBA", image.size, "white")
        shifted.paste(image, (int(width * 0.04), 0), image)
        image = shifted
    elif kind == "annotation_collision":
        draw = ImageDraw.Draw(image, "RGBA")
        draw.rectangle((0, int(height * 0.42), width, int(height * 0.49)), fill=(255, 255, 255, 170))
        image = image.filter(ImageFilter.GaussianBlur(0.15))
    elif kind == "information_density":
        image = image.resize((max(1, int(width * 0.82)), max(1, int(height * 0.82))), Image.Resampling.NEAREST).resize((width, height), Image.Resampling.NEAREST)
    else:
        raise ValueError(f"unsupported degradation kind: {kind}")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return {"source": str(source), "output": str(output), "degradation_kind": kind}


class AutoVisualJudge:
    """Small runtime facade used by the orchestrator or a Codex-side driver."""

    def __init__(self, calibration_floor: float = 0.90) -> None:
        self.calibration_floor = calibration_floor

    def pair(self, forward: dict[str, Any], reverse: dict[str, Any]) -> dict[str, Any]:
        return judge_pair(forward, reverse)

    def calibrate(self, rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
        return calibrate(rows, self.calibration_floor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pair = sub.add_parser("pair", help="validate forward/reverse swapped responses")
    pair.add_argument("--forward", type=Path, required=True)
    pair.add_argument("--reverse", type=Path, required=True)
    pair.add_argument("--output", type=Path)
    calibration = sub.add_parser("calibrate", help="score known original/degraded judge cases")
    calibration.add_argument("cases", type=Path, help="JSONL rows with original_id, forward, and reverse")
    calibration.add_argument("--floor", type=float, default=0.90)
    calibration.add_argument("--output", type=Path)
    degrade = sub.add_parser("degrade", help="create a deterministic calibration image")
    degrade.add_argument("source", type=Path)
    degrade.add_argument("output", type=Path)
    degrade.add_argument("--kind", choices=["text_too_small", "panel_spacing", "palette_contrast", "panel_alignment", "annotation_collision", "information_density"], required=True)
    args = parser.parse_args()
    try:
        if args.command == "pair":
            report = judge_pair(_load(args.forward), _load(args.reverse))
        elif args.command == "calibrate":
            rows = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
            report = calibrate(rows, args.floor)
        else:
            report = degrade_image(args.source, args.output, args.kind)
    except (OSError, json.JSONDecodeError, TypeError, ValueError, RuntimeError) as exc:
        print(f"AUTO VISUAL JUDGE: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if report.get("accepted", report.get("passed", True)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
