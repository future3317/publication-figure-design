#!/usr/bin/env python3
"""Prepare source-render variants and QA evidence for visual inspection.

These are not skill-generated candidates. The script never invents preference
judgments, calibration scores, Champion evidence, or deletes existing local output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from publication_figure_design.qa.technical import run_hard_qa


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "reference-benchmarks" / "real_generation_tasks.json"
OUT_ROOT = ROOT / "tmp" / "visual_sprint"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fit_canvas(source: Image.Image, *, width: int = 1600, background: tuple[int, int, int, int] = (255, 255, 255, 255)) -> Image.Image:
    image = source.convert("RGBA")
    scale = min(width / image.width, width / image.height)
    resized = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (width, max(1, round(resized.height + width * 0.04))), background)
    x = (canvas.width - resized.width) // 2
    y = (canvas.height - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def _render_candidates(source_path: Path, task_dir: Path) -> dict[str, Path]:
    source = Image.open(source_path)
    balanced = _fit_canvas(source)

    # Structure-first intentionally prioritizes panel footprint over fine styling;
    # the crop is visible but keeps all scientific marks intact for a fair judge.
    structure = balanced.crop((36, 24, balanced.width - 36, balanced.height - 24)).resize(balanced.size, Image.Resampling.LANCZOS)
    structure = ImageOps.expand(structure, border=(0, 10, 0, 10), fill=(248, 249, 250, 255)).crop((0, 10, balanced.width, balanced.height + 10))

    # Style-first changes only the visual treatment: muted contrast and a cool
    # editorial wash.  It never rewrites labels or data pixels semantically.
    style = ImageEnhance.Contrast(balanced).enhance(0.78)
    style = ImageEnhance.Color(style).enhance(0.84)
    wash = Image.new("RGBA", style.size, (246, 248, 250, 44))
    style = Image.alpha_composite(style, wash).filter(ImageFilter.GaussianBlur(0.12))

    outputs = {
        "structure-first": task_dir / "structure-first.png",
        "style-first": task_dir / "style-first.png",
        "balanced": task_dir / "balanced.png",
    }
    structure.save(outputs["structure-first"], optimize=True)
    style.save(outputs["style-first"], optimize=True)
    balanced.save(outputs["balanced"], optimize=True)
    return outputs


def _run_task(task: dict[str, Any], task_dir: Path) -> dict[str, Any]:
    task_id = str(task["id"])
    family = str(task["figure_family"])
    source = Path(str(task["source_image"]))
    task_dir.mkdir(parents=True, exist_ok=True)
    outputs = _render_candidates(source, task_dir)
    candidate_ids = [f"{family}__structure-first", f"{family}__style-first", f"{family}__balanced"]
    candidate_paths = {candidate_ids[0]: outputs["structure-first"], candidate_ids[1]: outputs["style-first"], candidate_ids[2]: outputs["balanced"]}

    qa = {}
    for candidate_id, path in candidate_paths.items():
        qa[candidate_id] = {"L0": run_hard_qa(path)}

    return {
        "id": task_id,
        "figure_family": family,
        "figure_type": task["figure_type"],
        "source_image": str(source),
        "source_sha256": _sha256(source),
        "source_code": str(task.get("source_code", "")),
        "candidate_ids": candidate_ids,
        "candidate_paths": {key: str(value) for key, value in candidate_paths.items()},
        "qa": qa,
        "repair_iterations": 0,
        "generation_method": "source_render_variant",
}


def _write_contact_sheets(report: dict[str, Any]) -> None:
    """Create small visual-review sheets for every focus family."""
    sheet_root = OUT_ROOT / "contact_sheets"
    sheet_root.mkdir(parents=True, exist_ok=True)
    for family, rows in report["families"].items():
        columns, tile_width, tile_height, label_height = 3, 520, 360, 34
        sheet = Image.new("RGB", (columns * tile_width, 2 * (tile_height + label_height)), "#eef1f3")
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(rows):
            column, line = index % columns, index // columns
            x, y = column * tile_width, line * (tile_height + label_height)
            image = Image.open(row["candidate_paths"][f"{family}__balanced"]).convert("RGB")
            image.thumbnail((tile_width - 16, tile_height - 16), Image.Resampling.LANCZOS)
            sheet.paste(image, (x + (tile_width - image.width) // 2, y + (tile_height - image.height) // 2))
            draw.text((x + 8, y + tile_height + 7), f"{row['id']} | balanced", fill="#26333d")
        sheet.save(sheet_root / f"{family}.png")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output", type=Path, default=OUT_ROOT / "sprint_report.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    tasks = manifest.get("tasks", [])
    if len(tasks) != 25:
        raise SystemExit(f"expected exactly 25 real tasks, found {len(tasks)}")
    missing = [str(task["source_image"]) for task in tasks if not Path(str(task["source_image"])).is_file()]
    if missing:
        raise SystemExit("missing source images:\n" + "\n".join(missing))
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    results = [_run_task(task, OUT_ROOT / "tasks" / str(task["id"])) for task in tasks]
    report = {
        "schema_version": "1.0",
        "manifest": str(args.manifest),
        "task_count": len(results),
        "candidate_count": len(results) * 3,
        "families": {family: [row for row in results if row["figure_family"] == family] for family in sorted({row["figure_family"] for row in results})},
        "tasks": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_contact_sheets(report)
    print(json.dumps({key: report[key] for key in ("task_count", "candidate_count")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
