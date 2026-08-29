#!/usr/bin/env python3
"""Run lightweight, deterministic checks on a TikZ/PGFPlots source file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def check_tex_source(source: str | Path) -> dict[str, object]:
    path = Path(source)
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, str] = {}
    if path.suffix.lower() != ".tex":
        errors.append("TeX source must use a .tex extension")
        return {"ok": False, "path": str(path), "errors": errors, "warnings": warnings, "checks": checks}
    if not path.is_file():
        errors.append(f"TeX source does not exist: {path}")
        return {"ok": False, "path": str(path), "errors": errors, "warnings": warnings, "checks": checks}
    text = path.read_text(encoding="utf-8", errors="replace")

    unsafe = [token for token in (r"\write18", "--shell-escape", "-shell-escape") if token in text]
    if unsafe:
        errors.append("unrestricted shell escape is present in TeX source: " + ", ".join(unsafe))
        checks["shell_escape"] = "fail"
    else:
        checks["shell_escape"] = "pass"

    if text.count(r"\begin{document}") != text.count(r"\end{document}"):
        errors.append("TeX document environment is unbalanced")
        checks["document_environment"] = "fail"
    else:
        checks["document_environment"] = "pass"

    uses_axis = r"\begin{axis}" in text or r"\addplot" in text
    uses_tikz = r"tikzpicture" in text or r"\draw" in text or r"\node" in text
    if uses_axis and "pgfplots" not in text:
        warnings.append("PGFPlots elements detected without an explicit pgfplots package declaration")
    if uses_tikz and "tikz" not in text.lower():
        warnings.append("TikZ elements detected without an explicit tikz package declaration")
    if "pgfplots" in text.lower() and "compat=" not in text.lower():
        warnings.append("PGFPlots source does not pin a compat version")
        checks["pgfplots_compat"] = "warn"
    elif "pgfplots" in text.lower():
        checks["pgfplots_compat"] = "pass"
    else:
        checks["pgfplots_compat"] = "not_applicable"

    if uses_axis and not any(token in text for token in ("width=", "height=", r"\linewidth", r"\columnwidth")):
        warnings.append("axis has no visible physical-size binding (width/height/linewidth/columnwidth)")
        checks["physical_size_binding"] = "warn"
    else:
        checks["physical_size_binding"] = "pass" if uses_axis else "not_applicable"
    return {"ok": not errors, "path": str(path), "errors": errors, "warnings": warnings, "checks": checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = check_tex_source(args.source)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"TeX source contract: {'PASS' if report['ok'] else 'FAIL'}")
        for item in report["errors"]:
            print(f"  ERROR: {item}")
        for item in report["warnings"]:
            print(f"  WARN: {item}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
