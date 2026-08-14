#!/usr/bin/env python3
"""Build equal-size source/reconstruction sheets for manual visual review."""

from __future__ import annotations

import argparse
import json
import math
import warnings
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _load(path: Path) -> Image.Image:
    warnings.simplefilter("ignore", Image.DecompressionBombWarning)
    previous = Image.MAX_IMAGE_PIXELS
    try:
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(path) as image:
            return image.convert("RGB")
    finally:
        Image.MAX_IMAGE_PIXELS = previous


def _fit(image: Image.Image, width: int, height: int) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail((width, height), Image.Resampling.LANCZOS)
    return fitted


def build_review_sheets(
    skill_root: Path,
    nature_root: Path,
    figures_root: Path,
    output_dir: Path,
    rows_per_sheet: int = 6,
) -> list[Path]:
    manifest = json.loads(
        (skill_root / "assets/visual-references/source-reconstruction-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    records = manifest["records"]
    output_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    cell_width, cell_height, label_height = 900, 390, 52
    source_width = cell_width // 2
    outputs: list[Path] = []

    for sheet_index in range(math.ceil(len(records) / rows_per_sheet)):
        batch = records[sheet_index * rows_per_sheet : (sheet_index + 1) * rows_per_sheet]
        canvas = Image.new(
            "RGB", (cell_width, len(batch) * (cell_height + label_height)), "#eef1f3"
        )
        draw = ImageDraw.Draw(canvas)
        for local_index, record in enumerate(batch):
            index = sheet_index * rows_per_sheet + local_index
            y = local_index * (cell_height + label_height)
            source_root = nature_root if record["repository"] == "nature-figure" else figures_root
            source = _fit(_load(source_root / record["relative_path"]), source_width - 20, cell_height - 20)
            reconstruction = _fit(_load(skill_root / record["image_path"]), source_width - 20, cell_height - 20)
            canvas.paste(source, ((source_width - source.width) // 2, y + 8 + (cell_height - source.height) // 2))
            canvas.paste(
                reconstruction,
                (source_width + (source_width - reconstruction.width) // 2, y + 8 + (cell_height - reconstruction.height) // 2),
            )
            draw.line((source_width, y, source_width, y + cell_height), fill="#c8d0d5", width=1)
            blueprint = record["reconstruction_blueprint"]["blueprint_id"]
            draw.text((8, y + cell_height + 4), f"{index + 1:02d}  SOURCE", fill="#25323b", font=font)
            draw.text((source_width + 8, y + cell_height + 4), "RECONSTRUCTION", fill="#25323b", font=font)
            draw.text((8, y + cell_height + 20), record["relative_path"], fill="#5b6872", font=font)
            draw.text((8, y + cell_height + 36), blueprint, fill="#5b6872", font=font)
        output = output_dir / f"source-reconstruction-review-{sheet_index + 1:02d}.png"
        canvas.save(output)
        outputs.append(output)
        for local_index, record in enumerate(batch):
            source_root = nature_root if record["repository"] == "nature-figure" else figures_root
            source = _fit(_load(source_root / record["relative_path"]), source_width - 20, cell_height - 20)
            reconstruction = _fit(_load(skill_root / record["image_path"]), source_width - 20, cell_height - 20)
            pair = Image.new("RGB", (cell_width, cell_height), "#eef1f3")
            pair.paste(source, ((source_width - source.width) // 2, 8 + (cell_height - source.height) // 2))
            pair.paste(reconstruction, (source_width + (source_width - reconstruction.width) // 2, 8 + (cell_height - reconstruction.height) // 2))
            ImageDraw.Draw(pair).line((source_width, 0, source_width, cell_height), fill="#c8d0d5", width=1)
            evidence = output_dir / "pairs" / f"{sheet_index * rows_per_sheet + local_index + 1:02d}-{record['archive_id']}.png"
            evidence.parent.mkdir(parents=True, exist_ok=True)
            pair.save(evidence)
    report = {
        "sheet_count": len(outputs),
        "record_count": len(records),
        "sheets": [path.name for path in outputs],
        "review_contract": [
            "Inspect source and reconstruction at equal size.",
            "Record topology, mark/layer type, hierarchy, whitespace, legend/annotation, and legibility.",
            "A failed fidelity check leaves the item pending; it cannot enter retrieval.",
        ],
    }
    (output_dir / "review-index.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nature-root", required=True, type=Path)
    parser.add_argument("--figures-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--rows-per-sheet", type=int, default=6)
    args = parser.parse_args()
    if args.rows_per_sheet < 1:
        raise ValueError("--rows-per-sheet must be positive")
    for path in build_review_sheets(
        args.skill_root, args.nature_root, args.figures_root, args.output_dir, args.rows_per_sheet
    ):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
