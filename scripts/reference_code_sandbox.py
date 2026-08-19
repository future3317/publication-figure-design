#!/usr/bin/env python3
"""Constrained runner for legacy reference-local reproduction scripts.

Reference intake itself never executes these files.  This helper is only for a
trusted, explicitly requested reproduction audit and rejects network/process
imports before launching in an isolated temporary working directory.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable


ALLOWED_IMPORTS = {"matplotlib", "numpy", "pandas", "PIL", "scipy", "seaborn", "reference_reconstruction"}
BLOCKED_IMPORTS = {"socket", "requests", "urllib", "http", "ftplib", "subprocess", "multiprocessing", "ctypes", "win32api", "pathlib"}
BLOCKED_CALLS = {"system", "popen", "run", "Popen", "check_call", "check_output", "create_connection"}


def validate_source(path: Path) -> list[str]:
    failures: list[str] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [f"cannot parse source: {exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
            for name in names:
                if name in BLOCKED_IMPORTS or name not in ALLOWED_IMPORTS:
                    failures.append(f"import not allowed: {name}")
        elif isinstance(node, ast.ImportFrom):
            name = (node.module or "").split(".")[0]
            if name in BLOCKED_IMPORTS or name not in ALLOWED_IMPORTS:
                failures.append(f"import not allowed: {name}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in BLOCKED_CALLS:
            failures.append(f"blocked call: {node.func.attr}")
    return sorted(set(failures))


def run_reference_code(code_path: Path, *, cwd: Path, output: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    failures = validate_source(code_path)
    if failures:
        raise ValueError("reference code sandbox rejected source: " + "; ".join(failures))
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONNOUSERSITE": "1",
        "MPLBACKEND": "Agg",
        "PFD_SANDBOX": "1",
        "TEMP": str(cwd),
        "TMP": str(cwd),
        "TMPDIR": str(cwd),
    }
    with tempfile.TemporaryDirectory(prefix="pfd-reference-sandbox-") as sandbox:
        sandbox_path = Path(sandbox)
        command = [sys.executable, str(code_path)]
        source = code_path.read_text(encoding="utf-8", errors="replace")
        if "--output" in source:
            command.extend(["--output", str(output)])
        return subprocess.run(command, cwd=sandbox_path, env=env, capture_output=True, text=True, timeout=timeout)
