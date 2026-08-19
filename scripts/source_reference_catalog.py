#!/usr/bin/env python3
"""Catalog original visual samples separately from independent reconstructions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from source_reconstruction_library import discover_sources, reconstruction_blueprint

try:
    from .reference_library import ReferenceLibrary
except ImportError:  # pragma: no cover - standalone CLI
    from reference_library import ReferenceLibrary


def catalog_source_images(
    nature_root: Path | str, figures_root: Path | str, skill_root: Path | str
) -> dict[str, Any]:
    """Copy declared source images into the private exact-reference catalog once."""
    skill_root = Path(skill_root)
    records = discover_sources(nature_root, figures_root)
    library = ReferenceLibrary(root=skill_root, registry_path=skill_root / "assets/registry.jsonl")
    created = 0
    output: list[dict[str, Any]] = []
    for record in records:
        ref_id = record.source_sha256[:16]
        existing = library.get(ref_id)
        if existing is None:
            reference = library.ingest(
                record.source_path,
                figure_type=record.visual_family,
                scope="references",
                metadata_override={
                    "reference_kind": "exact_visual_source",
                    "subtype": reconstruction_blueprint(record)["blueprint_id"],
                    "tags": ["source-catalog", record.repository, record.visual_family],
                    "layout": "multi-panel" if len(reconstruction_blueprint(record)["panel_recipes"]) > 1 else "single-panel",
                    "source": f"{record.repository} visual source",
                    "source_url": None,
                    "license": record.license_class,
                    "usage_scope": "internal_reference",
                    "review_status": "pending",
                    "aesthetic_rating": None,
                    "production_ready": False,
                    "notes": "Exact source visual sample cataloged for private reference; distinct from independent reconstruction.",
                    "source_fingerprint": record.source_sha256,
                    "source_repository": record.repository,
                    "source_relative_path": record.relative_path,
                    "source_license_class": record.license_class,
                    "source_action": record.source_action,
                    "visual_family": record.visual_family,
                    "reconstruction_blueprint": reconstruction_blueprint(record),
                },
            )
            created += 1
        else:
            reference = existing
            metadata = reference.metadata
            metadata.update({
                "reference_kind": "exact_visual_source",
                "subtype": reconstruction_blueprint(record)["blueprint_id"],
                "source_fingerprint": record.source_sha256,
                "source_repository": record.repository,
                "source_relative_path": record.relative_path,
                "source_license_class": record.license_class,
                "source_action": record.source_action,
                "visual_family": record.visual_family,
                "reconstruction_blueprint": reconstruction_blueprint(record),
            })
            (skill_root / "assets/visual-references/references" / reference.id / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        output.append(
            {
                "reference_id": reference.id,
                "source_fingerprint": record.source_sha256,
                "repository": record.repository,
                "relative_path": record.relative_path,
                "visual_family": record.visual_family,
                "blueprint_id": reconstruction_blueprint(record)["blueprint_id"],
                "reconstruction_blueprint": reconstruction_blueprint(record),
            }
        )
    catalog_path = skill_root / "assets/visual-references/source-reference-catalog.json"
    catalog_path.write_text(
        json.dumps({"cataloged_count": len(output), "records": output}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    library.rebuild_registry()
    return {"cataloged_count": len(output), "created_count": created, "records": output}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nature-root", required=True, type=Path)
    parser.add_argument("--figures-root", required=True, type=Path)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(catalog_source_images(args.nature_root, args.figures_root, args.skill_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
