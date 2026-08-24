"""L0 hard technical checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


def run_hard_qa(figure: str | Path, packet: Mapping[str, Any] | None = None, trace: Mapping[str, Any] | None = None) -> dict[str, Any]:
    path = Path(figure)
    issues: list[str] = []
    if not path.is_file() or path.stat().st_size == 0:
        issues.append("figure output is missing or empty")
    if packet and not (packet.get("style_tokens") or packet.get("journal_profile")):
        issues.append("design packet has no compiled style or journal constraints")
    journal = dict((packet or {}).get("journal_profile") or {})
    if journal.get("status") == "placeholder" or journal.get("verified") is False and journal.get("name") in {"science", "cell"}:
        issues.append("journal profile is a placeholder; technical submission certification is blocked")
    return {"layer": "L0_hard_technical", "passed": not issues, "issues": issues, "checks": {"exists": not issues}}
