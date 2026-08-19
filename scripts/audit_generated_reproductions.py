#!/usr/bin/env python3
"""Render and audit every generated-archive reproduction in the reference library."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from reference_image_analysis import analyze_image, compare_images
from reference_library import ReferenceLibrary


AUDIT_RELATIVE = Path("assets/visual-references/review-evidence/generated-reproduction-audit.json")
PAIR_DIRNAME = "generated-reproduction-audit"
SOURCE_MANIFEST_RELATIVE = Path("assets/visual-references/source-reconstruction-manifest.json")


def _resolve(root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else root / path


def check_record_paths(root: Path | str, metadata: dict[str, Any]) -> list[str]:
    """Return missing lifecycle artifacts for one generated reference."""
    root = Path(root)
    findings: list[str] = []
    for field in ("image_path", "code_path", "reproduction_preview_path", "figure_card_path"):
        value = metadata.get(field)
        if not value:
            findings.append(field)
            continue
        path = _resolve(root, str(value))
        if path is None or not path.is_file():
            findings.append(field)
    return findings


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _make_pair(first: Path, second: Path, output: Path, label_a: str = "stored", label_b: str = "fresh render") -> None:
    with Image.open(first) as first_open, Image.open(second) as second_open:
        cells: list[Image.Image] = []
        for opened in (first_open, second_open):
            image = opened.convert("RGB")
            image.thumbnail((480, 340), Image.Resampling.LANCZOS)
            cell = Image.new("RGB", (480, 340), "white")
            cell.paste(image, ((480 - image.width) // 2, (340 - image.height) // 2))
            cells.append(cell)
    sheet = Image.new("RGB", (960, 370), "#eef1f3")
    sheet.paste(cells[0], (0, 0))
    sheet.paste(cells[1], (480, 0))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((8, 348), label_a, fill="#26333d", font=font)
    draw.text((488, 348), label_b, fill="#26333d", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def _sync_source_manifest_hashes(root: Path) -> int:
    """Refresh generated output hashes after preview synchronization.

    The source manifest is an audit index, not the registry source of truth, but
    its output hash must still describe the current generated preview.  Keeping
    this update in the same command prevents a successful render audit from
    leaving a stale manifest that fails the next lifecycle check.
    """
    manifest_path = root / SOURCE_MANIFEST_RELATIVE
    if not manifest_path.is_file():
        return 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    changed = 0
    for item in manifest.get("records", []):
        image_path = _resolve(root, item.get("image_path"))
        if image_path is None or not image_path.is_file():
            continue
        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if item.get("output_sha256") != digest:
            item["output_sha256"] = digest
            changed += 1
    if changed:
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return changed


def _render(code_path: Path, archive_dir: Path, workdir: Path) -> tuple[subprocess.CompletedProcess[str], Path | None]:
    """Render a code file using its declared CLI shape."""
    stale = archive_dir / "reproduced.png"
    if stale.exists():
        stale.unlink()
    output = workdir / "fresh-render.png"
    code_text = code_path.read_text(encoding="utf-8", errors="replace")
    command = [sys.executable, str(code_path)]
    if "--output" in code_text:
        command.extend(["--output", str(output)])
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")
    completed = subprocess.run(
        command,
        cwd=archive_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if not output.is_file() and stale.is_file():
        shutil.copy2(stale, output)
        stale.unlink()
    return completed, output if output.is_file() else None


def audit_generated_reproductions(
    skill_root: Path | str,
    *,
    mark_visual_inspection: bool = False,
    render: bool = True,
    sync_previews: bool = False,
) -> dict[str, Any]:
    root = Path(skill_root)
    generated_root = root / "assets/visual-references/generated-archive"
    audit_path = root / AUDIT_RELATIVE
    pair_root = audit_path.parent / PAIR_DIRNAME
    records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="publication_figure_generated_audit_") as tmp_name:
        tmp_root = Path(tmp_name)
        for metadata_path in sorted(generated_root.glob("*/metadata.json")):
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            archive_dir = metadata_path.parent
            image_path = _resolve(root, metadata.get("image_path")) or (archive_dir / "image.png")
            code_path = _resolve(root, metadata.get("code_path")) or (archive_dir / "code.py")
            card_path = archive_dir / "figure_card.json"
            metadata["figure_card_path"] = _relative(root, card_path)
            metadata["reproduction_preview_path"] = metadata.get("image_path") or _relative(root, image_path)
            analyze_image(
                image_path,
                output=card_path,
                figure_type=str(metadata.get("figure_type", "unknown")),
                source=str(metadata.get("source", "generated reference")),
            )
            metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

            findings = check_record_paths(root, metadata)
            item: dict[str, Any] = {
                "id": metadata.get("id", archive_dir.name),
                "figure_type": metadata.get("figure_type"),
                "source": metadata.get("source"),
                "image_path": metadata.get("image_path"),
                "code_path": metadata.get("code_path"),
                "figure_card_path": metadata.get("figure_card_path"),
                "reproduction_preview_path": metadata.get("reproduction_preview_path"),
                "path_findings": findings,
                "render": {"status": "not_run"},
                "pixel_consistency": {"status": "not_run"},
                "visual_inspection": {
                    "status": "inspected_contact_sheet" if mark_visual_inspection else "pending",
                    "method": "stored-vs-fresh-render contact sheet" if mark_visual_inspection else None,
                },
            }
            if render and not findings:
                workdir = tmp_root / archive_dir.name
                workdir.mkdir(parents=True, exist_ok=True)
                try:
                    completed, rendered = _render(code_path, archive_dir, workdir)
                    item["render"] = {
                        "status": "pass" if completed.returncode == 0 and rendered else "fail",
                        "returncode": completed.returncode,
                        "stderr_tail": completed.stderr[-500:],
                    }
                    if rendered:
                        if sync_previews:
                            shutil.copy2(rendered, image_path)
                            metadata["sha256"] = hashlib.sha256(image_path.read_bytes()).hexdigest()
                            analyze_image(
                                image_path,
                                output=card_path,
                                figure_type=str(metadata.get("figure_type", "unknown")),
                                source=str(metadata.get("source", "generated reference")),
                            )
                            metadata_path.write_text(
                                json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                            )
                        comparison = compare_images(image_path, rendered)
                        item["pixel_consistency"] = {
                            **comparison,
                            "status": "pass" if comparison.get("size_match") and (comparison.get("ssim") or 0) >= 0.995 else "needs_review",
                        }
                        pair_path = pair_root / f"{item['id']}-stored-vs-fresh.png"
                        _make_pair(image_path, rendered, pair_path)
                        item["stored_vs_fresh_path"] = _relative(root, pair_path)
                except (OSError, subprocess.SubprocessError) as exc:
                    item["render"] = {"status": "fail", "error": str(exc)}
            records.append(item)

    summary = {
        "schema": "publication-figure-design/generated-reproduction-audit",
        "policy": {
            "generated_archive_is_reconstruction": True,
            "pixel_consistency_does_not_certify_source_fidelity": True,
            "source_fidelity_remains_separate": True,
        },
        "summary": {
            "checked": len(records),
            "path_failures": sum(bool(item["path_findings"]) for item in records),
            "render_pass": sum(item["render"].get("status") == "pass" for item in records),
            "pixel_consistency_pass": sum(item["pixel_consistency"].get("status") == "pass" for item in records),
            "visual_inspection_pending": sum(item["visual_inspection"].get("status") == "pending" for item in records),
        },
        "records": records,
    }
    if sync_previews:
        summary["summary"]["source_manifest_hashes_synced"] = _sync_source_manifest_hashes(root)
        ReferenceLibrary(
            root=root, registry_path=root / "assets/registry.jsonl"
        ).rebuild_registry()
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--visual-inspected", action="store_true")
    parser.add_argument("--sync-previews", action="store_true")
    args = parser.parse_args()
    report = audit_generated_reproductions(
        args.skill_root,
        mark_visual_inspection=args.visual_inspected,
        render=not args.no_render,
        sync_previews=args.sync_previews,
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0 if report["summary"]["path_failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
