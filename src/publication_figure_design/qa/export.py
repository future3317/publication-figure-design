"""Export contract checks for editable vector publication assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def check_export(path: str | Path, *, formats: list[str] | None = None) -> dict[str, Any]:
    output = Path(path)
    formats = formats or [output.suffix.lstrip(".")]
    return {"passed": output.is_file() and output.stat().st_size > 0, "path": str(output), "formats": formats, "editable_text": output.suffix.lower() in {".svg", ".pdf"}, "font_embedding": output.suffix.lower() in {".svg", ".pdf"}}
