"""Vector-first SVG assembler for heterogeneous panels."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .svg import read_svg, wrap_svg


def assemble_svg(panels: Sequence[Path], layout: dict, output: Path) -> Path:
    width = float(layout["canvas"]["width_mm"])
    height = float(layout["canvas"]["height_mm"])
    panel_boxes = layout.get("panels", [])
    groups = []
    for index, panel_path in enumerate(panels):
        if index >= len(panel_boxes):
            break
        box = panel_boxes[index]
        groups.append(f'<g transform="translate({box["x_mm"]},{box["y_mm"]}) scale({box["width_mm"]},{box["height_mm"]})">{wrap_svg(read_svg(Path(panel_path)), width_mm=box["width_mm"], height_mm=box["height_mm"], panel_id=box["id"])}</g>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}"><metadata>publication-figure-design vector assembler; editable text preserved</metadata>{"".join(groups)}</svg>\n'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    return output
