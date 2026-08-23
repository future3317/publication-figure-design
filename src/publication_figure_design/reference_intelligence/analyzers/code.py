"""Static plotting-code analyzer; never imports or executes reference code."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Mapping

from ..dna import ReferenceDNA


def analyze_code(path: Path, *, metadata: Mapping[str, Any] | None = None) -> ReferenceDNA:
    source = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(path))
    calls: list[str] = []
    literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else "call"
            calls.append(fn)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and (node.value.startswith("#") or re.fullmatch(r"[A-Za-z]+", node.value)):
            literals.append(node.value)
    meta = dict(metadata or {})
    meta.setdefault("reference_kind", "code")
    dna = ReferenceDNA.from_metadata(meta)
    dna.identity["source_kind"] = "code"
    dna.geometry.update({"plot_calls": sorted(set(calls)), "line_count": len(source.splitlines())})
    dna.palette["code_literals"] = sorted(set(literals))
    dna.typography["exactness"] = "code_declared"
    dna.confidence.update({"geometry": 0.94, "palette": 0.86, "typography": 0.82})
    dna.extensions["code"] = {"calls": sorted(set(calls)), "static_only": True}
    return dna
