"""Low-cost deterministic publication candidate generation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..reference_intelligence.dna import DesignPacket


def generate_candidates(packet: DesignPacket, mode: str = "publication") -> list[dict[str, Any]]:
    if mode not in {"fast", "standard", "publication"}:
        raise ValueError("mode must be fast, standard, or publication")
    count = {"fast": 1, "standard": 2, "publication": 3}[mode]
    variants = [
        ("structure-first", {"layout_priority": "structure", "legend_strategy": "shared_compact"}),
        ("style-first", {"layout_priority": "style", "legend_strategy": "direct_then_shared"}),
        ("balanced", {"layout_priority": "balanced", "legend_strategy": "task_compatible"}),
    ]
    packet.candidates = []
    for name, overrides in variants[:count]:
        packet.candidates.append({"id": name, "mode": mode, "dpi": 120, "scientific_contract": deepcopy(packet.scientific_contract), "style_tokens": deepcopy(packet.style_tokens), "overrides": overrides, "status": "draft"})
    return packet.candidates
