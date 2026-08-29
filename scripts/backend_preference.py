#!/usr/bin/env python3
"""Read or write the explicit plotting-backend preference for this skill.

Adapted from Yuan1z0825/nature-skills (Apache-2.0), nature-figure backend helper.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


VALID_BACKENDS = {"python", "r", "tex"}


def config_path() -> Path:
    override = os.environ.get("ACADEMIC_FIGURE_CONFIG")
    if override:
        return Path(override).expanduser()
    return Path("~/.config/publication-figure-design/preferences.json").expanduser()


def read_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid backend preference file at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid backend preference file at {path}: expected an object")
    return data


def get_backend(path: Path) -> str | None:
    backend = read_config(path).get("backend")
    return backend if backend in VALID_BACKENDS else None


def set_backend(path: Path, backend: str) -> str:
    normalized = backend.lower()
    if normalized not in VALID_BACKENDS:
        raise ValueError("backend must be one of: python, r, tex")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"backend": normalized}, indent=2) + "\n", encoding="utf-8")
    return normalized


def clear_backend(path: Path) -> None:
    if path.exists():
        path.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("get")
    setter = commands.add_parser("set")
    setter.add_argument("backend", choices=sorted(VALID_BACKENDS))
    commands.add_parser("clear")
    commands.add_parser("path")
    args = parser.parse_args(argv)
    path = config_path()
    if args.command == "get":
        backend = get_backend(path)
        if backend is None:
            return 1
        print(backend)
        return 0
    if args.command == "set":
        print(set_backend(path, args.backend))
        return 0
    if args.command == "clear":
        clear_backend(path)
        return 0
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
