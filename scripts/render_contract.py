"""Compatibility import for the package-owned renderer contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication_figure_design.render_contract import (  # noqa: E402,F401
    REQUIRED_SPECS,
    strict_renderer_payload,
    validate_render_contract,
)

__all__ = ["REQUIRED_SPECS", "strict_renderer_payload", "validate_render_contract"]
