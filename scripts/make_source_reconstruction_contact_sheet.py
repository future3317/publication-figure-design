#!/usr/bin/env python3
"""Create a compact visual QA sheet from the installed reconstruction manifest."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def make_contact_sheet(skill_root: Path, output: Path, columns: int = 6) -> Path:
    manifest = json.loads(
        (skill_root / "assets/visual-references/source-reconstruction-manifest.json").read_text(encoding="utf-8")
    )
    records = manifest["records"]
    tile_width, tile_height, label_height = 300, 210, 38
    rows = math.ceil(len(records) / columns)
    sheet = Image.new("RGB", (columns * tile_width, rows * (tile_height + label_height)), "#eef1f3")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, record in enumerate(records):
        row, column = divmod(index, columns)
        x, y = column * tile_width, row * (tile_height + label_height)
        with Image.open(skill_root / record["image_path"]) as image:
            image = image.convert("RGB")
            image.thumbnail((tile_width - 12, tile_height - 12), Image.Resampling.LANCZOS)
            px = x + (tile_width - image.width) // 2
            py = y + (tile_height - image.height) // 2
            sheet.paste(image, (px, py))
        label = f"{index + 1:02d} {record['repository']} | {record['visual_family']}"
        draw.text((x + 6, y + tile_height + 4), label, fill="#26333d", font=font)
        short_path = Path(record["relative_path"]).name[:42]
        draw.text((x + 6, y + tile_height + 20), short_path, fill="#5b6872", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=90)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(make_contact_sheet(args.skill_root, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
