# -*- coding: utf-8 -*-
"""Light-weight Production Asset metadata manager for publication-figure-design.

This module scans ``assets/figures/<type>/metadata.json`` sidecars and helps
agents decide whether a production asset is safe to COPY-FIRST or only useful
as visual inspiration.

Design principles
-----------------
* **One sidecar per figure type.** The metadata lives next to the script and
  preview so it is easy to discover and maintain.
* **No changes to existing scripts.** Phase 4 only adds JSON sidecars for a
  small pilot set; unannotated assets fall back to the existing full-script
  inspection workflow.
* **Promotion is gated.** A visual reference is promoted only when it has been
  reviewed and marked ``production_ready``.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from .reference_library import ReferenceLibrary
except ImportError:  # pragma: no cover - allow standalone import during dev
    from reference_library import ReferenceLibrary


__all__ = [
    "PRODUCTION_METADATA_FIELDS",
    "ProductionAsset",
    "ProductionAssetLibrary",
]


# ---------------------------------------------------------------------------
# Constants & schema
# ---------------------------------------------------------------------------

_ALLOWED_ASSET_KINDS = {"template", "reusable", "example"}
_ALLOWED_RUNTIMES = {"python", "r", "tex", "mixed"}
_ALLOWED_PALETTE_POLICIES = {"preserve", "adaptable"}

_REQUIRED_FIELDS = ["id", "figure_type", "asset_kind", "runtime", "production_ready"]

PRODUCTION_METADATA_FIELDS = [
    "id",
    "figure_type",
    "variant",
    "asset_kind",
    "runtime",
    "dependencies",
    "data_shape",
    "grouping",
    "preview",
    "palette_policy",
    "production_ready",
    "notes",
]

_DEFAULT_METADATA = {
    "variant": "default",
    "dependencies": [],
    "data_shape": None,
    "grouping": None,
    "preview": None,
    "palette_policy": "adaptable",
    "production_ready": False,
    "notes": None,
}


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _resolve_skill_root() -> Path:
    """Return the repository root by looking for SKILL.md."""
    script_dir = Path(__file__).resolve().parent
    candidates = [script_dir.parent, script_dir.parent.parent]
    for candidate in candidates:
        if (candidate / "SKILL.md").exists():
            return candidate
    return script_dir.parent


SKILL_ROOT = _resolve_skill_root()
FIGURES_DIR = SKILL_ROOT / "assets" / "figures"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class ProductionAsset:
    """In-memory representation of one production asset metadata entry."""

    def __init__(self, metadata: Dict[str, Any], root: Path = SKILL_ROOT):
        self.metadata = metadata
        self.root = Path(root)

    @property
    def id(self) -> str:
        return self.metadata["id"]

    @property
    def figure_type(self) -> str:
        return self.metadata["figure_type"]

    @property
    def variant(self) -> str:
        return self.metadata.get("variant", "default")

    @property
    def asset_kind(self) -> str:
        return self.metadata["asset_kind"]

    @property
    def runtime(self) -> str:
        return self.metadata["runtime"]

    @property
    def production_ready(self) -> bool:
        return bool(self.metadata.get("production_ready", False))

    @property
    def preview(self) -> Optional[Path]:
        p = self.metadata.get("preview")
        if not p:
            return None
        return self.directory / p

    @property
    def directory(self) -> Path:
        return self.root / "assets" / "figures" / self.figure_type

    def to_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self.metadata)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.metadata, indent=indent, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _normalise_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Apply defaults and coerce types."""
    out = copy.deepcopy(_DEFAULT_METADATA)
    out.update(metadata)

    # Coerce boolean.
    pr = out.get("production_ready")
    if isinstance(pr, str):
        out["production_ready"] = pr.lower() in {"true", "1", "yes"}
    else:
        out["production_ready"] = bool(pr)

    # Coerce dependencies to list of strings.
    deps = out.get("dependencies")
    if deps is None:
        out["dependencies"] = []
    elif isinstance(deps, str):
        out["dependencies"] = [d.strip() for d in deps.split(",") if d.strip()]
    else:
        out["dependencies"] = [str(d).strip() for d in deps]

    return out


def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a production metadata dict after applying defaults."""
    errors: List[str] = []

    # Check required fields on the raw input first, because defaults should not
    # hide a missing required field.
    for field in _REQUIRED_FIELDS:
        if field not in metadata or metadata[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    try:
        meta = _normalise_metadata(metadata)
    except (TypeError, ValueError) as exc:
        return False, errors + [str(exc)]

    if meta.get("asset_kind") not in _ALLOWED_ASSET_KINDS:
        errors.append(
            f"Invalid asset_kind {meta.get('asset_kind')!r}; "
            f"must be one of {_ALLOWED_ASSET_KINDS}"
        )

    if meta.get("runtime") not in _ALLOWED_RUNTIMES:
        errors.append(
            f"Invalid runtime {meta.get('runtime')!r}; "
            f"must be one of {_ALLOWED_RUNTIMES}"
        )

    policy = meta.get("palette_policy")
    if policy is not None and policy not in _ALLOWED_PALETTE_POLICIES:
        errors.append(
            f"Invalid palette_policy {policy!r}; "
            f"must be one of {_ALLOWED_PALETTE_POLICIES}"
        )

    deps = meta.get("dependencies")
    if deps is not None and not isinstance(deps, list):
        errors.append("dependencies must be a list")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------

class ProductionAssetLibrary:
    """Manage production asset metadata sidecars."""

    def __init__(self, root: Path = SKILL_ROOT):
        self.root = Path(root)
        self._assets: Dict[str, ProductionAsset] = {}

    def _figures_dir(self) -> Path:
        return self.root / "assets" / "figures"

    def scan(self, force: bool = False) -> List[ProductionAsset]:
        """Discover all ``metadata.json`` files under ``assets/figures/``.

        Parameters
        ----------
        force : bool
            If True, clear the in-memory cache and rescan from disk.
        """
        if force:
            self._assets.clear()

        figures_dir = self._figures_dir()
        if not figures_dir.exists():
            return []

        found: List[ProductionAsset] = []
        for fig_dir in sorted(figures_dir.iterdir()):
            if not fig_dir.is_dir():
                continue
            meta_path = fig_dir / "metadata.json"
            if not meta_path.exists():
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                # Skip broken sidecars; validate() will report them.
                continue
            asset = ProductionAsset(meta, self.root)
            self._assets[asset.id] = asset
            found.append(asset)
        return found

    def get(self, asset_id: str) -> Optional[ProductionAsset]:
        """Return a production asset by id, scanning if necessary."""
        if asset_id in self._assets:
            return self._assets[asset_id]
        self.scan()
        return self._assets.get(asset_id)

    def get_by_path(
        self, figure_type: str, variant: str = "default"
    ) -> Optional[ProductionAsset]:
        """Return the asset for a given figure type directory and variant."""
        self.scan()
        for asset in self._assets.values():
            if asset.figure_type == figure_type and asset.variant == variant:
                return asset
        return None

    def list(
        self,
        figure_type: Optional[str] = None,
        asset_kind: Optional[str] = None,
        runtime: Optional[str] = None,
        production_ready: Optional[bool] = None,
    ) -> List[ProductionAsset]:
        """List assets with optional filters."""
        results = []
        for asset in self.scan():
            if figure_type is not None and asset.figure_type != figure_type:
                continue
            if asset_kind is not None and asset.asset_kind != asset_kind:
                continue
            if runtime is not None and asset.runtime != runtime:
                continue
            if production_ready is not None and asset.production_ready != production_ready:
                continue
            results.append(asset)
        return results

    def query(
        self,
        figure_type: str,
        data_shape: Optional[str] = None,
        grouping: Optional[str] = None,
        runtime: Optional[str] = None,
        production_ready: Optional[bool] = True,
        limit: Optional[int] = None,
    ) -> List[ProductionAsset]:
        """Query production assets by figure type and optional filters.

        Default ``production_ready=True`` because agents usually want assets
        they can safely reuse.
        """
        results = []
        for asset in self.scan():
            if asset.figure_type != figure_type:
                continue
            if production_ready is not None and asset.production_ready != production_ready:
                continue
            if runtime is not None and asset.runtime != runtime:
                continue
            if data_shape is not None and asset.metadata.get("data_shape") != data_shape:
                continue
            if grouping is not None and asset.metadata.get("grouping") != grouping:
                continue
            results.append(asset)

        # Stable ordering: production_ready first, then template > reusable > example.
        kind_order = {"template": 0, "reusable": 1, "example": 2}
        results.sort(
            key=lambda a: (
                0 if a.production_ready else 1,
                kind_order.get(a.asset_kind, 99),
                a.id,
            )
        )

        if limit is not None:
            results = results[:limit]
        return results

    def validate(self) -> Tuple[bool, List[Tuple[str, List[str]]]]:
        """Validate every ``metadata.json`` found under ``assets/figures/``."""
        problems: List[Tuple[str, List[str]]] = []
        all_ok = True
        figures_dir = self._figures_dir()
        if not figures_dir.exists():
            return True, []

        for fig_dir in sorted(figures_dir.iterdir()):
            if not fig_dir.is_dir():
                continue
            meta_path = fig_dir / "metadata.json"
            if not meta_path.exists():
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                all_ok = False
                problems.append((fig_dir.name, [f"Invalid JSON: {exc}"]))
                continue
            ok, errors = validate_metadata(meta)
            if not ok:
                all_ok = False
                problems.append((fig_dir.name, errors))
        return all_ok, problems

    def promote_from_visual_reference(
        self,
        ref_id: str,
        target_variant: str = "default",
        notes: Optional[str] = None,
    ) -> ProductionAsset:
        """Promote a reviewed visual reference to a production asset.

        The reference must have ``review_status="reviewed"`` and
        ``production_ready=true``. The original reference is left untouched;
        this method copies its archived code (if any) and image into
        ``assets/figures/<figure_type>/`` and writes a ``metadata.json``.
        """
        ref_lib = ReferenceLibrary(root=self.root)
        ref = ref_lib.get(ref_id)
        if ref is None:
            raise ValueError(f"Visual reference {ref_id!r} not found.")

        m = ref.metadata
        if m.get("review_status") != "reviewed":
            raise ValueError(
                f"Reference {ref_id} has review_status={m.get('review_status')!r}; "
                "only reviewed references can be promoted."
            )
        if not m.get("production_ready"):
            raise ValueError(
                f"Reference {ref_id} is not marked production_ready."
            )

        figure_type = m.get("figure_type")
        if not figure_type:
            raise ValueError(f"Reference {ref_id} has no figure_type.")

        target_dir = self._figures_dir() / figure_type
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy image.
        src_image = ref.image_path
        if src_image is None or not src_image.exists():
            raise ValueError(f"Reference {ref_id} has no image to promote.")
        dest_image = target_dir / src_image.name
        shutil.copy2(str(src_image), str(dest_image))

        # Copy code if available.
        src_code = ref.code_path
        dest_code: Optional[Path] = None
        if src_code is not None and src_code.exists():
            dest_code = target_dir / src_code.name
            shutil.copy2(str(src_code), str(dest_code))

        asset_id = f"{figure_type.lower()}_{target_variant}"
        meta = {
            "id": asset_id,
            "figure_type": figure_type,
            "variant": target_variant,
            "asset_kind": "template",
            "runtime": "python",  # Default; user should edit after review.
            "dependencies": [],
            "data_shape": m.get("data_shape"),
            "grouping": m.get("grouping"),
            "preview": dest_image.name,
            "palette_policy": m.get("palette_policy", "adaptable"),
            "production_ready": True,
            "notes": notes or m.get("notes") or f"Promoted from visual reference {ref_id}.",
        }
        if dest_code is not None:
            meta["script"] = dest_code.name

        meta = _normalise_metadata(meta)
        valid, errors = validate_metadata(meta)
        if not valid:
            raise ValueError(f"Generated metadata invalid: {'; '.join(errors)}")

        meta_path = target_dir / "metadata.json"
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )

        asset = ProductionAsset(meta, self.root)
        self._assets[asset.id] = asset
        return asset


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _pretty_print(asset: ProductionAsset) -> None:
    print(asset.to_json(indent=2))
    print()


def cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Production Asset metadata manager for publication-figure-design."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="Scan assets/figures/ for metadata sidecars.")

    list_p = sub.add_parser("list", help="List production assets.")
    list_p.add_argument("--figure-type")
    list_p.add_argument("--asset-kind", choices=sorted(_ALLOWED_ASSET_KINDS))
    list_p.add_argument("--runtime", choices=sorted(_ALLOWED_RUNTIMES))
    list_p.add_argument(
        "--production-ready",
        type=lambda x: x.lower() == "true",
        default=None,
    )

    query_p = sub.add_parser("query", help="Query production assets.")
    query_p.add_argument("figure_type")
    query_p.add_argument("--data-shape")
    query_p.add_argument("--grouping")
    query_p.add_argument("--runtime", choices=sorted(_ALLOWED_RUNTIMES))
    query_p.add_argument(
        "--production-ready",
        type=lambda x: x.lower() == "true",
        default=True,
    )
    query_p.add_argument("--limit", type=int)

    sub.add_parser("validate", help="Validate all metadata sidecars.")

    promote_p = sub.add_parser(
        "promote",
        help="Promote a reviewed visual reference to a production asset.",
    )
    promote_p.add_argument("ref_id", help="Visual reference id.")
    promote_p.add_argument("--variant", default="default")
    promote_p.add_argument("--notes")

    args = parser.parse_args(argv)
    lib = ProductionAssetLibrary()

    if args.command == "scan":
        assets = lib.scan(force=True)
        print(f"Found {len(assets)} production asset(s)")
        return 0

    if args.command == "list":
        assets = lib.list(
            figure_type=args.figure_type,
            asset_kind=args.asset_kind,
            runtime=args.runtime,
            production_ready=args.production_ready,
        )
        print(f"Found {len(assets)} asset(s)")
        for asset in assets:
            _pretty_print(asset)
        return 0

    if args.command == "query":
        assets = lib.query(
            figure_type=args.figure_type,
            data_shape=args.data_shape,
            grouping=args.grouping,
            runtime=args.runtime,
            production_ready=args.production_ready,
            limit=args.limit,
        )
        print(f"Found {len(assets)} asset(s)")
        for asset in assets:
            _pretty_print(asset)
        return 0

    if args.command == "validate":
        ok, problems = lib.validate()
        if ok:
            print("All production metadata sidecars are valid.")
            return 0
        for dirname, errors in problems:
            print(f"{dirname}: {'; '.join(errors)}")
        return 1

    if args.command == "promote":
        asset = lib.promote_from_visual_reference(
            ref_id=args.ref_id,
            target_variant=args.variant,
            notes=args.notes,
        )
        print(f"Promoted to production asset: {asset.id}")
        _pretty_print(asset)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(cli())
