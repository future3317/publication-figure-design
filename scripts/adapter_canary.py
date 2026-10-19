#!/usr/bin/env python3
"""Static agent-adapter canary for Claude/Codex/Cursor/Copilot loaders."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "claude-code": [ROOT / "install" / "claude-code" / "README.md"],
    "codex": [ROOT / "install" / "codex" / "manifest.yaml", ROOT / "install" / "codex" / "instructions.md"],
    "cursor": [ROOT / "install" / "cursor" / ".cursorrules"],
    "copilot": [ROOT / "install" / "copilot" / "copilot-instructions.md"],
}
def run() -> dict:
    failures: list[str] = []
    canonical = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    rows = []
    for target, paths in TARGETS.items():
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.is_file())
        if not text:
            failures.append(f"{target}: adapter files missing")
            continue
        if "SKILL.md" not in text:
            failures.append(f"{target}: loader does not identify SKILL.md")
        if "does not draw the figure" not in canonical or "inspect the actual output" not in canonical:
            failures.append("canonical skill must require a rendered figure and actual output inspection")
        rows.append({"target": target, "skill_loader": "present"})
    return {
        "scope": "static adapter-loader contract; does not test model triggering",
        "targets": rows,
        "failures": failures,
        "passed": not failures,
    }


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["passed"] else 1)
