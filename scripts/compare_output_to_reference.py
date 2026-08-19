#!/usr/bin/env python3
"""Compare a rendered output against a concrete visual reference.

Usage: ``python scripts/compare_output_to_reference.py --reference ref.png --output out.png``
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication_figure_design.qa.compare import compare_output_to_reference  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_pos", nargs="?")
    parser.add_argument("output_pos", nargs="?")
    parser.add_argument("--reference", dest="reference")
    parser.add_argument("--output", dest="output")
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args(argv)
    reference, output = args.reference or args.reference_pos, args.output or args.output_pos
    if not reference or not output:
        parser.error("reference and output are required")
    report = compare_output_to_reference(reference, output)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.json_path:
        args.json_path.write_text(text + "\n", encoding="utf-8")
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
