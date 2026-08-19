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
PROMPTS = {
    "figure": "rebuild this Nature multi-panel figure from the supplied reference and run final QA",
    "review": "review an existing scientific figure for typography, palette, layout and export fidelity",
}


def run() -> dict:
    failures: list[str] = []
    canonical = (ROOT / "SKILL.md").read_text(encoding="utf-8") + (ROOT / "manifest.yaml").read_text(encoding="utf-8")
    rows = []
    for target, paths in TARGETS.items():
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.is_file())
        if not text:
            failures.append(f"{target}: adapter files missing")
            continue
        required = ("SKILL.md", "reference")
        missing = [token for token in required if token.lower() not in text.lower()]
        if missing:
            failures.append(f"{target}: missing loader contract {missing}")
        if "QA" not in canonical or "route" not in canonical.lower():
            failures.append("canonical skill is missing QA/route contract")
        rows.append({"target": target, "prompt_count": len(PROMPTS), "route": "reference-first" if "reference" in text.lower() else "missing"})
    return {"targets": rows, "failures": failures, "passed": not failures}


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["passed"] else 1)
