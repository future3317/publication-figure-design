#!/usr/bin/env python3
"""Compile a StyleSpec sidecar into renderer tokens or a prompt."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from publication_figure_design.style.compiler import (  # noqa: E402
    StyleSpec,
    apply_style_spec_svg,
    build_image_generation_style_prompt,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--backend", choices=("svg", "prompt", "json"), default="json")
    args = parser.parse_args(argv)
    spec = StyleSpec.from_dict(json.loads(args.spec.read_text(encoding="utf-8")))
    if args.backend == "svg":
        value = apply_style_spec_svg(spec)
    elif args.backend == "prompt":
        value = build_image_generation_style_prompt(spec)
    else:
        value = spec.to_dict()
    print(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
