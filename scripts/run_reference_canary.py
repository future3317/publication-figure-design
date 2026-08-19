#!/usr/bin/env python3
"""Run retrieval and optional rendered-alignment canaries for one reference."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication_figure_design.references.retrieval.multi_role import MultiRoleReferenceRetriever  # noqa: E402
from publication_figure_design.style.compiler import StyleSpec, build_image_generation_style_prompt  # noqa: E402
from publication_figure_design.qa.compare import compare_output_to_reference  # noqa: E402


def run_canary(reference_id: str, candidate: Path | None = None, root: Path = ROOT) -> dict:
    metadata_path = root / "assets" / "visual-references" / "references" / reference_id / "metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Unknown reference: {reference_id}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    retriever = MultiRoleReferenceRetriever(root=root)
    roles = retriever.retrieve(
        figure_type=str(metadata.get("figure_type", "")),
        tags=metadata.get("tags", []),
        limit=3,
        layout=metadata.get("layout"),
    )
    queries = {
        "structure": [item.get("id") for item in roles.get("structure_reference", [])],
        "style": [item.get("id") for item in roles.get("style_reference", [])],
        "annotation": [item.get("id") for item in roles.get("annotation_reference", [])],
    }
    style_data = metadata.get("style_spec") or {
        "palette": {"roles": (metadata.get("visual_grammar") or {}).get("palette_roles", {})},
        "density": {"level": metadata.get("data_density", "moderate")},
    }
    prompt = build_image_generation_style_prompt(StyleSpec.from_dict(style_data))
    report = {
        "schema_version": "1.0",
        "reference_id": reference_id,
        "queries": queries,
        "retrieval_pass": any(reference_id in ids for ids in queries.values()),
        "style_prompt": prompt,
        "alignment": None,
    }
    if candidate is not None:
        report["alignment"] = compare_output_to_reference(
            root / metadata["image_path"], candidate
        )
        report["alignment_pass"] = report["alignment"]["verdict"] == "pass"
    else:
        report["alignment_pass"] = False
    report["canary_pass"] = bool(report["retrieval_pass"] and report["alignment_pass"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_id")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_canary(args.reference_id, args.candidate)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if report["canary_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
