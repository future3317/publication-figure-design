#!/usr/bin/env python3
"""Create a pixel-backed contact sheet for every generated-archive preview."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def make_contact_sheet(skill_root: Path | str, output: Path | str, columns: int = 6) -> Path:
    root = Path(skill_root)
    metadata_paths = sorted((root / "assets/visual-references/generated-archive").glob("*/metadata.json"))
    tile_width, tile_height, label_height = 300, 210, 38
    rows = math.ceil(len(metadata_paths) / columns)
    sheet = Image.new("RGB", (columns * tile_width, rows * (tile_height + label_height)), "#eef1f3")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, metadata_path in enumerate(metadata_paths):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        row, column = divmod(index, columns)
        x, y = column * tile_width, row * (tile_height + label_height)
        image_path = root / metadata["image_path"]
        with Image.open(image_path) as opened:
            image = opened.convert("RGB")
            image.thumbnail((tile_width - 12, tile_height - 12), Image.Resampling.LANCZOS)
            sheet.paste(image, (x + (tile_width - image.width) // 2, y + (tile_height - image.height) // 2))
        label = f"{index + 1:02d} {metadata.get('figure_type', 'unknown')}"
        draw.text((x + 6, y + tile_height + 4), label[:48], fill="#26333d", font=font)
        draw.text((x + 6, y + tile_height + 20), metadata_path.parent.name, fill="#5b6872", font=font)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
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
