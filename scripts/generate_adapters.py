#!/usr/bin/env python3
"""Generate thin cross-platform loaders from the canonical skill manifest."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


def _resolve_skill_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    for candidate in (script_dir.parent, script_dir.parent.parent):
        if (candidate / "SKILL.md").exists():
            return candidate
    return script_dir.parent


SKILL_ROOT = _resolve_skill_root()
MANIFEST = SKILL_ROOT / "manifest.yaml"
INSTALL_DIR = SKILL_ROOT / "install"


def _manifest_version() -> str:
    text = MANIFEST.read_text(encoding="utf-8")
    match = re.search(r"^version:\s*[\"']?([^\"'\s]+)", text, re.MULTILINE)
    if not match:
        raise RuntimeError("manifest.yaml must define a root version")
    return match.group(1)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _runtime_files() -> list[str]:
    # Keep the adapter bundle in lockstep with the canonical manifest.  The
    # parser is intentionally small because the runtime section is a flat list.
    lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    runtime: list[str] = []
    in_runtime = False
    for line in lines:
        if line.strip() == "runtime:":
            in_runtime = True
            continue
        if in_runtime and line and not line.startswith(" "):
            break
        if in_runtime:
            item = line.strip()
            if item.startswith("-"):
                runtime.append(item[1:].strip().strip("\"'"))
    if not runtime:
        raise RuntimeError("manifest.yaml runtime bundle is empty")
    return runtime


def _loader_header(host: str) -> str:
    version = _manifest_version()
    files = "\n".join(f"- `{item}`" for item in _runtime_files())
    return f"""# Publication Figure Design adapter — {host}

This is a thin loader for `publication-figure-design` manifest version `{version}`.
The canonical instructions and route contracts live in the bundled skill; this
file is not a replacement or a second source of design rules.

Runtime bundle:
{files}

Generated: {_now()}
"""


def generate_claude_code() -> str:
    return _loader_header("Claude Code") + """
Install this directory at `~/.claude/skills/publication-figure-design/`.
Load `SKILL.md` and resolve all relative scripts/resources from that directory.
"""


def generate_codex_manifest() -> tuple[str, str]:
    version = _manifest_version()
    manifest = f"""# Generated adapter metadata; package compatibility identifier only; one current workflow.
name: publication-figure-design
version: \"{version}\"
entrypoint: SKILL.md
source_manifest: manifest.yaml
runtime:
  - SKILL.md
  - manifest.yaml
  - references/
  - scripts/
  - assets/visual-references/
  - assets/registry.jsonl
  - schemas/
  - indexes/
"""
    instructions = _loader_header("OpenAI Codex") + """
Load `SKILL.md` as the instruction entrypoint. When a route names a script,
schema, index, or reference asset, use the bundled relative path; do not
substitute an adapter-local copy.
"""
    return manifest, instructions


def generate_cursor_rules() -> str:
    return _loader_header("Cursor") + """
For publication-figure tasks, load and follow the canonical `SKILL.md` and its
selected manifest route. Do not invent a local mini-version or bypass gates.
"""


def generate_copilot_instructions() -> str:
    return _loader_header("GitHub Copilot") + """
For publication-figure tasks, use the canonical `SKILL.md`, manifest route, and
bundled runtime files. These instructions only provide loading context.
"""


TARGETS = {"claude-code", "codex", "cursor", "copilot"}


def generate(target: str | None = None) -> None:
    targets = [target] if target else sorted(TARGETS)
    unknown = [item for item in targets if item not in TARGETS]
    if unknown:
        raise SystemExit(f"Unknown target(s): {', '.join(unknown)}")
    print(f"Publication Figure Design adapters — manifest {_manifest_version()}")
    for item in targets:
        out_dir = INSTALL_DIR / item
        out_dir.mkdir(parents=True, exist_ok=True)
        if item == "claude-code":
            (out_dir / "README.md").write_text(generate_claude_code(), encoding="utf-8")
        elif item == "codex":
            manifest, instructions = generate_codex_manifest()
            (out_dir / "manifest.yaml").write_text(manifest, encoding="utf-8")
            (out_dir / "instructions.md").write_text(instructions, encoding="utf-8")
        elif item == "cursor":
            (out_dir / ".cursorrules").write_text(generate_cursor_rules(), encoding="utf-8")
        else:
            (out_dir / "copilot-instructions.md").write_text(generate_copilot_instructions(), encoding="utf-8")
        print(f"[OK] {item}: {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=sorted(TARGETS))
    args = parser.parse_args()
    generate(args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
