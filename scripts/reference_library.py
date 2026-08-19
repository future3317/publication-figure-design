# -*- coding: utf-8 -*-
"""Light-weight Visual Reference Library for publication-figure-design.

This module manages visual references independently from production assets
(``assets/figures/``).  A visual reference is a single example image plus a
side-car metadata JSON file.  The registry index (``assets/registry.jsonl``)
is completely auto-generated from the side-car files and can be deleted and
rebuilt at any time.

Design principles
-----------------
* **Side-car metadata is the single source of truth.** ``registry.jsonl`` is
  only a fast lookup cache.
* **Relative paths only.** No local absolute paths (e.g. ``C:/Users/...``) are
  written to metadata.
* **Deterministic IDs.** IDs are derived from the SHA-256 of the image bytes,
  so the same image always maps to the same id.
* **Scope separation.** ``references/`` holds external images (papers,
  screenshots, GitHub examples); ``generated-archive/`` holds figures produced
  by the skill itself.
* **Aesthetic vs. production readiness are separate.** ``aesthetic_rating`` is
  a human quality judgment; ``production_ready`` marks whether the asset is a
  candidate for future COPY-FIRST promotion.
* **No embedding / CLIP / vector DB.** Queries are plain metadata filters.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import json as _json
import os
import shutil
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from PIL import Image
except ImportError:  # pragma: no cover - minimal runtimes may omit Pillow
    Image = None  # type: ignore[assignment,misc]

try:
    from .palette_manager import list_palettes, _normalize_name as _resolve_palette_name
except ImportError:  # pragma: no cover - allow standalone import during dev
    from palette_manager import list_palettes, _normalize_name as _resolve_palette_name

try:
    from .visual_grammar import validate_visual_grammar
except ImportError:  # pragma: no cover - allow standalone import during dev
    from visual_grammar import validate_visual_grammar


__all__ = [
    "REFERENCE_METADATA_FIELDS",
    "VisualReference",
    "ReferenceLibrary",
    "ingest_image",
    "archive_generated_figure",
    "cli",
    "normalize_figure_type",
]


# ---------------------------------------------------------------------------
# Constants & schema
# ---------------------------------------------------------------------------

# UTC timestamp format used throughout.
_UTC_FMT = "%Y-%m-%dT%H:%M:%SZ"

# Allowed scopes for a visual reference.
_SCOPES = {"references", "generated-archive"}

# Allowed review statuses.
_REVIEW_STATUSES = {"pending", "reviewed", "rejected", "promoted"}
_LIFECYCLE_STATES = {"raw", "analyzed", "reviewed", "benchmarked", "production", "rejected"}

# Allowed usage scopes.  This field expresses copyright / redistribution scope
# only.  Template maturity is expressed by ``review_status`` and
# ``production_ready``, not by ``usage_scope``.
_USAGE_SCOPES = {"private_reference", "internal_reference", "redistributable"}

# Allowed palette policies.
_PALETTE_POLICIES = {"preserve", "adaptable"}

# Required metadata fields.
_REQUIRED_FIELDS = ["id", "scope", "figure_type", "image_path", "created_at"]

# All fields we recognise and validate.
REFERENCE_METADATA_FIELDS = [
    "id",
    "scope",
    "figure_type",
    "subtype",
    "tags",
    "palette",
    "palette_policy",
    "layout",
    "journal_style",
    "source",
    "source_url",
    "author",
    "venue",
    "year",
    "license",
    "usage_scope",
    "allowed_usage",
    "image_path",
    "preview_path",
    "thumbnail_path",
    "dimensions",
    "colorspace",
    "has_alpha",
    "perceptual_hash",
    "aliases",
    "code_path",
    "reproduction_preview_path",
    "figure_card_path",
    "review_status",
    "lifecycle_state",
    "quarantine",
    "aesthetic_rating",
    "production_ready",
    "n_groups",
    "data_density",
    "notes",
    "visual_grammar",
    "visual_review",
    "reference_kind",
    "created_at",
]

# Default values applied during validation/ingest.
_DEFAULT_METADATA = {
    "scope": "references",
    "subtype": None,
    "tags": [],
    "palette": None,
    "palette_policy": "preserve",
    "layout": None,
    "journal_style": None,
    "source": "unknown",
    "source_url": None,
    "author": None,
    "venue": None,
    "year": None,
    "license": "unknown",
    "usage_scope": "private_reference",
    "allowed_usage": ["private_reference"],
    "preview_path": None,
    "thumbnail_path": None,
    "dimensions": None,
    "colorspace": None,
    "has_alpha": None,
    "perceptual_hash": None,
    "aliases": [],
    "code_path": None,
    "reproduction_preview_path": None,
    "figure_card_path": None,
    "review_status": "pending",
    "lifecycle_state": "raw",
    "quarantine": {},
    "aesthetic_rating": None,
    "production_ready": False,
    "n_groups": None,
    "data_density": None,
    "notes": None,
    "visual_grammar": None,
    "reference_kind": "derived_reference",
    # Intake state is deliberately separate from review_status.  The
    # latter remains for compatibility and retrieval ranking.
    "original_quality": "unassessed",
    "analysis_quality": "unassessed",
    "reconstruction_fidelity": "unassessed",
    "eligible_for_structure": False,
    "eligible_for_style": False,
    "eligible_for_code_reuse": False,
    "eligible_for_reconstruction": False,
}

_FIGURE_TYPE_ALIASES = {
    "bar": "grouped_bar", "bar_chart": "grouped_bar", "bar_grouped": "grouped_bar",
    "groupedbar": "grouped_bar", "grouped_bar": "grouped_bar",
    "barcomparison": "grouped_bar", "bar_comparison": "grouped_bar",
    "heatmap": "heatmap_grid", "heat_map": "heatmap_grid", "heatmap_grid": "heatmap_grid",
    "scatter": "scatter_bubble", "scatterplot": "scatter_bubble",
    "scatter_plot": "scatter_bubble", "scatter_bubble": "scatter_bubble",
}


def normalize_figure_type(value: str) -> str:
    """Return a stable snake-case figure taxonomy key with common aliases."""
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value).strip())
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    return _FIGURE_TYPE_ALIASES.get(text, text)


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
    # Fallback: assume we are two levels below the skill root.
    return script_dir.parent


SKILL_ROOT = _resolve_skill_root()
VISUAL_REFS_DIR = SKILL_ROOT / "assets" / "visual-references"
REGISTRY_PATH = SKILL_ROOT / "assets" / "registry.jsonl"


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _visual_refs_rel(*parts: str) -> str:
    """Return a path string relative to the skill root under visual-references."""
    return (Path("assets") / "visual-references" / Path(*parts)).as_posix()


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class VisualReference:
    """In-memory representation of one visual reference entry."""

    def __init__(self, metadata: Dict[str, Any], root: Path = SKILL_ROOT):
        self.metadata = metadata
        self.root = Path(root)

    @property
    def id(self) -> str:
        return self.metadata["id"]

    @property
    def scope(self) -> str:
        return self.metadata.get("scope", "references")

    @property
    def figure_type(self) -> str:
        return normalize_figure_type(self.metadata.get("figure_type", ""))

    @property
    def image_path(self) -> Optional[Path]:
        p = self.metadata.get("image_path")
        return self.root / p if p else None

    @property
    def code_path(self) -> Optional[Path]:
        p = self.metadata.get("code_path")
        return self.root / p if p else None

    @property
    def preview_path(self) -> Optional[Path]:
        p = self.metadata.get("preview_path")
        return self.root / p if p else None

    @property
    def thumbnail_path(self) -> Optional[Path]:
        p = self.metadata.get("thumbnail_path")
        return self.root / p if p else None

    def to_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self.metadata)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.metadata, indent=indent, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _short_id(sha256_hex: str, length: int = 16) -> str:
    return sha256_hex[:length]


def _perceptual_hash(image: Any) -> Optional[str]:
    """Return a small deterministic DCT perceptual hash for a PIL image.

    This intentionally has no external dependency.  It is used only for
    near-duplicate intake detection; SHA-256 remains the canonical identity.
    """
    if Image is None:
        return None
    try:
        gray = image.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
        pixels = __import__("numpy").asarray(gray, dtype=float)
        n = pixels.shape[0]
        basis = __import__("numpy").cos(
            __import__("numpy").pi * (2 * __import__("numpy").arange(n)[:, None] + 1)
            * __import__("numpy").arange(8)[None, :] / (2 * n)
        )
        coeff = basis.T @ pixels @ basis
        low = coeff[:8, :8]
        threshold = float(__import__("numpy").median(low[1:, 1:]))
        bits = (low >= threshold).astype(int).flatten()
        return "".join(f"{int(bits[i:i + 4].dot([8, 4, 2, 1])):x}" for i in range(0, 64, 4))
    except Exception:
        return None


def _phash_distance(first: Optional[str], second: Optional[str]) -> Optional[int]:
    if not first or not second or len(first) != len(second):
        return None
    try:
        return sum((int(a, 16) ^ int(b, 16)).bit_count() for a, b in zip(first, second))
    except ValueError:
        return None


def _image_intake_facts(path: Path) -> Dict[str, Any]:
    """Read objective pixel facts and emit sRGB derivatives when possible."""
    facts: Dict[str, Any] = {
        "dimensions": None,
        "colorspace": None,
        "has_alpha": None,
        "perceptual_hash": None,
    }
    if Image is None:
        return facts
    try:
        with Image.open(path) as opened:
            facts["dimensions"] = [int(opened.width), int(opened.height)]
            facts["has_alpha"] = "A" in opened.getbands() or "transparency" in opened.info
            facts["colorspace"] = "embedded_icc" if opened.info.get("icc_profile") else "sRGB_assumed"
            facts["perceptual_hash"] = _perceptual_hash(opened)
    except Exception:
        # Reference intake must remain compatible with legacy placeholder files
        # and formats unsupported by Pillow; validation still protects bytes.
        return facts
    return facts


def _write_derivatives(source: Path, asset_dir: Path, root: Optional[Path] = None) -> Dict[str, Optional[str]]:
    """Create canonical sRGB preview and thumbnail sidecars if decodable."""
    result: Dict[str, Optional[str]] = {"preview_path": None, "thumbnail_path": None}
    if Image is None:
        return result
    try:
        with Image.open(source) as opened:
            image = opened.convert("RGBA") if "A" in opened.getbands() else opened.convert("RGB")
            preview = image.copy()
            preview.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            preview_path = asset_dir / "preview.png"
            preview.save(preview_path, format="PNG", optimize=True)
            thumb = image.copy()
            thumb.thumbnail((320, 320), Image.Resampling.LANCZOS)
            thumb_path = asset_dir / "thumbnail.png"
            thumb.save(thumb_path, format="PNG", optimize=True)
            result["preview_path"] = _as_relative(preview_path, root or _resolve_skill_root())
            result["thumbnail_path"] = _as_relative(thumb_path, root or _resolve_skill_root())
    except Exception:
        return result
    return result


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime(_UTC_FMT)


def _as_relative(path: Any, root: Path = SKILL_ROOT) -> str:
    """Convert *path* to a forward-slash relative path below *root*.

    Raises ValueError if the path is outside *root* or absolute.
    """
    if path is None:
        return None  # type: ignore[return-value]
    p = Path(path)
    root = Path(root).resolve()
    if p.is_absolute():
        try:
            p = p.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError(
                f"Absolute path {path!r} is outside the skill root {root}; "
                "only project-relative paths are allowed."
            ) from exc
    rel = p.as_posix()
    if rel.startswith(".."):
        raise ValueError(f"Path {path!r} resolves outside the skill root.")
    return rel


def validate_metadata(metadata: Dict[str, Any], root: Path = SKILL_ROOT) -> Tuple[bool, List[str]]:
    """Validate a metadata dict after applying defaults.

    Returns (is_valid, list_of_errors).
    """
    errors: List[str] = []

    # Normalise defaults first so we don't reject raw metadata that simply
    # omits optional fields.
    try:
        meta = _normalise_metadata(metadata, root)
    except ValueError as exc:
        return False, [str(exc)]

    for field in _REQUIRED_FIELDS:
        if field not in meta or meta[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    if meta.get("scope") not in _SCOPES:
        errors.append(
            f"Invalid scope {meta.get('scope')!r}; must be one of {_SCOPES}"
        )

    if meta.get("review_status") not in _REVIEW_STATUSES:
        errors.append(
            f"Invalid review_status {meta.get('review_status')!r}; "
            f"must be one of {_REVIEW_STATUSES}"
        )

    lifecycle_state = meta.get("lifecycle_state")
    if lifecycle_state not in _LIFECYCLE_STATES:
        errors.append(
            f"Invalid lifecycle_state {lifecycle_state!r}; must be one of {_LIFECYCLE_STATES}"
        )
    if not isinstance(meta.get("quarantine"), dict):
        errors.append("quarantine must be an object")

    if meta.get("usage_scope") not in _USAGE_SCOPES:
        errors.append(
            f"Invalid usage_scope {meta.get('usage_scope')!r}; "
            f"must be one of {_USAGE_SCOPES}"
        )

    allowed_usage = meta.get("allowed_usage")
    if not isinstance(allowed_usage, list) or not all(isinstance(item, str) for item in allowed_usage):
        errors.append("allowed_usage must be a list of strings")

    dimensions = meta.get("dimensions")
    if dimensions is not None and (
        not isinstance(dimensions, list) or len(dimensions) != 2
        or not all(isinstance(value, int) and value > 0 for value in dimensions)
    ):
        errors.append("dimensions must be [positive width, positive height]")

    for key in ("preview_path", "thumbnail_path"):
        value = meta.get(key)
        if value is not None:
            try:
                _as_relative(value, root)
            except ValueError as exc:
                errors.append(f"Invalid {key}: {exc}")

    palette_policy = meta.get("palette_policy")
    if palette_policy is not None and palette_policy not in _PALETTE_POLICIES:
        errors.append(
            f"Invalid palette_policy {palette_policy!r}; "
            f"must be one of {_PALETTE_POLICIES}"
        )

    rating = meta.get("aesthetic_rating")
    if rating is not None and (not isinstance(rating, (int, float)) or rating < 0 or rating > 5):
        errors.append("aesthetic_rating must be a number between 0 and 5")

    production_ready = meta.get("production_ready")
    if production_ready is not None and not isinstance(production_ready, bool):
        errors.append("production_ready must be a boolean")

    tags = meta.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append("tags must be a list")

    # Validate image_path is relative and inside project.
    try:
        _as_relative(meta.get("image_path"))
    except ValueError as exc:
        errors.append(f"Invalid image_path: {exc}")

    # Validate optional code_path similarly.
    code_path = meta.get("code_path")
    if code_path is not None:
        try:
            _as_relative(code_path)
        except ValueError as exc:
            errors.append(f"Invalid code_path: {exc}")

    preview_path = meta.get("reproduction_preview_path")
    if preview_path is not None:
        try:
            _as_relative(preview_path)
        except ValueError as exc:
            errors.append(f"Invalid reproduction_preview_path: {exc}")

    figure_card_path = meta.get("figure_card_path")
    if figure_card_path is not None:
        try:
            _as_relative(figure_card_path)
        except ValueError as exc:
            errors.append(f"Invalid figure_card_path: {exc}")

    # Validate palette if provided.
    palette = meta.get("palette")
    if palette is not None:
        try:
            _resolve_palette_name(palette)
        except ValueError as exc:
            errors.append(f"Invalid palette: {exc}")

    if meta.get("visual_grammar") is not None:
        errors.extend(validate_visual_grammar(meta["visual_grammar"]))

    return len(errors) == 0, errors


def _normalise_metadata(metadata: Dict[str, Any], root: Path = SKILL_ROOT) -> Dict[str, Any]:
    """Apply defaults, coerce types, and make paths relative."""
    out = copy.deepcopy(_DEFAULT_METADATA)
    out.update(metadata)

    if out.get("figure_type"):
        out["figure_type"] = normalize_figure_type(out["figure_type"])

    # Ensure created_at exists.
    if not out.get("created_at"):
        out["created_at"] = _now_utc()

    # Coerce boolean fields.
    for key in ("production_ready",):
        val = out.get(key)
        if isinstance(val, str):
            out[key] = val.lower() in {"true", "1", "yes"}

    # Coerce tags to list of strings.
    tags = out.get("tags")
    if tags is None:
        out["tags"] = []
    elif isinstance(tags, str):
        out["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    else:
        out["tags"] = [str(t).strip() for t in tags]

    # Normalise paths relative to the library root.
    out["image_path"] = _as_relative(out.get("image_path"), root)
    if out.get("code_path") is not None:
        out["code_path"] = _as_relative(out["code_path"], root)
    if out.get("reproduction_preview_path") is not None:
        out["reproduction_preview_path"] = _as_relative(out["reproduction_preview_path"], root)
    if out.get("figure_card_path") is not None:
        out["figure_card_path"] = _as_relative(out["figure_card_path"], root)
    for key in ("preview_path", "thumbnail_path"):
        if out.get(key) is not None:
            out[key] = _as_relative(out[key], root)

    aliases = out.get("aliases")
    if aliases is None:
        out["aliases"] = []
    elif not isinstance(aliases, list):
        out["aliases"] = [aliases]

    # Drop unknown top-level fields?  Keep them but warn during validate.
    return out


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------

class ReferenceLibrary:
    """Manage the visual reference collection."""

    def __init__(self, root: Path = SKILL_ROOT, registry_path: Path = REGISTRY_PATH):
        self.root = Path(root)
        self.registry_path = Path(registry_path)
        self._refs: Dict[str, VisualReference] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _visual_refs_dir(self) -> Path:
        return self.root / "assets" / "visual-references"

    def _asset_dir(self, ref_id: str, scope: str) -> Path:
        return self._visual_refs_dir() / scope / ref_id

    def _metadata_path(self, ref_id: str, scope: str) -> Path:
        return self._asset_dir(ref_id, scope) / "metadata.json"

    def _image_name_from_source(self, source_path: Path) -> str:
        """Keep original extension, but normalise the name."""
        ext = source_path.suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".gif", ".webp"}:
            ext = ".png"
        return f"image{ext}"

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def ingest(
        self,
        image_path: Path,
        figure_type: str,
        scope: str = "references",
        metadata_override: Optional[Dict[str, Any]] = None,
        copy: bool = True,
    ) -> VisualReference:
        """Add an external image to the reference library.

        Parameters
        ----------
        image_path : Path
            Source image file. May be outside the skill root.
        figure_type : str
            Logical figure type (e.g. "GroupedViolin").
        scope : {"references", "generated-archive"}
            Where to store the asset.
        metadata_override : dict, optional
            Extra metadata fields merged on top of defaults.
        copy : bool, default True
            If True, copy the image into the library; otherwise move it.

        Returns
        -------
        VisualReference

        Raises
        ------
        ValueError
            If the same image (by SHA-256) is already in the library.
            IDs are deterministic, so duplicate images always map to the same id.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image_bytes = image_path.read_bytes()
        sha256_hex = _sha256_of_bytes(image_bytes)
        ref_id = _short_id(sha256_hex)
        intake_facts = _image_intake_facts(image_path)

        if scope not in _SCOPES:
            raise ValueError(f"Invalid scope {scope!r}; must be one of {_SCOPES}")

        # Duplicate detection.  Deterministic IDs mean the same image always
        # maps to the same reference; we keep a single asset record per image.
        existing = self.get(ref_id)
        if existing is not None:
            raise ValueError(
                f"Image already exists as reference {ref_id} "
                f"({existing.metadata.get('image_path')})."
            )

        # Near duplicates share one canonical source.  Preserve the incoming
        # provenance as an alias instead of creating another retrieval item.
        if intake_facts.get("perceptual_hash"):
            for candidate in self.all():
                distance = _phash_distance(
                    intake_facts.get("perceptual_hash"),
                    candidate.metadata.get("perceptual_hash"),
                )
                if distance is not None and distance <= 4:
                    aliases = list(candidate.metadata.get("aliases") or [])
                    aliases.append({
                        "sha256": sha256_hex,
                        "perceptual_hash": intake_facts["perceptual_hash"],
                        "source_name": image_path.name,
                    })
                    candidate.metadata["aliases"] = aliases
                    candidate.metadata["alias_reason"] = "near_duplicate_phash"
                    meta_path = self._metadata_path(candidate.id, candidate.scope)
                    meta_path.write_text(
                        json.dumps(candidate.metadata, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    self._refs[candidate.id] = candidate
                    return candidate

        asset_dir = self._asset_dir(ref_id, scope)
        asset_dir.mkdir(parents=True, exist_ok=True)
        dest_image = asset_dir / self._image_name_from_source(image_path)

        if copy:
            shutil.copy2(str(image_path), str(dest_image))
        else:
            shutil.move(str(image_path), str(dest_image))

        derivative_paths = _write_derivatives(dest_image, asset_dir, self.root)

        meta = {
            "id": ref_id,
            "scope": scope,
            "figure_type": figure_type,
            "image_path": _as_relative(dest_image, self.root),
            "sha256": sha256_hex,
        }
        meta.update(intake_facts)
        meta.update(derivative_paths)
        if metadata_override:
            meta.update(metadata_override)

        # Canonical pixel identity and generated derivative paths are measured
        # by intake, not user-editable sidecar overrides.
        meta["image_path"] = _as_relative(dest_image, self.root)
        meta["sha256"] = sha256_hex
        meta.update(intake_facts)
        meta.update(derivative_paths)

        # Ingest records provenance; it cannot grant its own aesthetic approval.
        meta.update({
            "review_status": "pending",
            "aesthetic_rating": None,
            "production_ready": False,
            "lifecycle_state": "raw",
            "quarantine": {"state": "raw", "history": []},
        })

        meta = _normalise_metadata(meta, self.root)
        valid, errors = validate_metadata(meta)
        if not valid:
            raise ValueError(f"Metadata validation failed: {'; '.join(errors)}")

        meta_path = asset_dir / "metadata.json"
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )

        ref = VisualReference(meta, self.root)
        self._refs[ref_id] = ref
        return ref

    def archive_generated_figure(
        self,
        image_path: Path,
        figure_type: str,
        code_path: Optional[Path] = None,
        metadata_override: Optional[Dict[str, Any]] = None,
        copy: bool = True,
    ) -> VisualReference:
        """Archive a figure produced by the skill itself.

        This is a convenience wrapper around ``ingest`` with sensible defaults
        for self-generated figures.  If ``code_path`` is provided, the code file
        is copied into the same asset directory and the metadata points to the
        archived copy.
        """
        override = {
            "scope": "generated-archive",
            "source": "self-generated",
            "usage_scope": "internal_reference",
            "review_status": "pending",
            "production_ready": False,
            # Note: production_ready + review_status express template maturity;
            # usage_scope only tracks redistribution rights.
        }
        if metadata_override:
            override.update(metadata_override)

        ref = self.ingest(
            image_path=image_path,
            figure_type=figure_type,
            scope="generated-archive",
            metadata_override=override,
            copy=copy,
        )

        if code_path is not None:
            code_path = Path(code_path)
            if code_path.exists():
                asset_dir = self._asset_dir(ref.id, "generated-archive")
                dest_code = asset_dir / f"code{code_path.suffix}"
                if copy:
                    shutil.copy2(str(code_path), str(dest_code))
                else:
                    shutil.move(str(code_path), str(dest_code))
                ref.metadata["code_path"] = _as_relative(dest_code, self.root)
                # Rewrite side-car with updated code_path.
                meta_path = asset_dir / "metadata.json"
                meta_path.write_text(
                    json.dumps(ref.metadata, indent=2, ensure_ascii=False, sort_keys=True),
                    encoding="utf-8",
                )
                # Update in-memory cache.
                self._refs[ref.id] = ref

        return ref

    def get(self, ref_id: str) -> Optional[VisualReference]:
        """Return a reference by id, or None if not found."""
        if ref_id in self._refs:
            return self._refs[ref_id]

        for scope in _SCOPES:
            meta_path = self._metadata_path(ref_id, scope)
            if meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                ref = VisualReference(meta, self.root)
                self._refs[ref_id] = ref
                return ref
        return None

    def review(
        self,
        ref_id: str,
        aesthetic_rating: float,
        visual_review: Dict[str, Any],
    ) -> VisualReference:
        """Record a completed rendered visual review for one pending reference."""
        required = {
            "final_size_inspected", "hierarchy", "panel_balance", "whitespace",
            "legend_footprint", "text_legibility", "reviewer",
        }
        missing = sorted(field for field in required if not visual_review.get(field))
        if visual_review.get("final_size_inspected") is not True:
            missing = sorted(set(missing) | {"final_size_inspected"})
        verdict_fields = required - {"final_size_inspected", "reviewer"}
        invalid = sorted(
            field for field in verdict_fields
            if visual_review.get(field) not in {"pass", "justified_deviation"}
        )
        if missing or invalid:
            details = []
            if missing:
                details.append("missing: " + ", ".join(missing))
            if invalid:
                details.append("invalid verdict: " + ", ".join(invalid))
            raise ValueError("Incomplete rendered visual review (" + "; ".join(details) + ").")
        if not isinstance(aesthetic_rating, (int, float)) or not 0 <= aesthetic_rating <= 5:
            raise ValueError("aesthetic_rating must be a number between 0 and 5")
        ref = self.get(ref_id)
        if ref is None:
            raise KeyError(f"Unknown visual reference: {ref_id}")
        if ref.metadata.get("reference_kind") == "user_supplied":
            code_path = ref.metadata.get("code_path")
            preview_path = ref.metadata.get("reproduction_preview_path")
            if not code_path or not (self.root / code_path).is_file():
                raise ValueError("User-supplied references require runnable reproduction code before review.")
            if not preview_path or not (self.root / preview_path).is_file():
                raise ValueError("User-supplied references require a rendered reproduction preview before review.")
            grammar_errors = validate_visual_grammar(ref.metadata.get("visual_grammar"))
            if grammar_errors:
                raise ValueError(
                    "User-supplied references require a complete visual grammar card before review: "
                    + "; ".join(grammar_errors)
                )
        ref.metadata.update({
            "review_status": "reviewed",
            "aesthetic_rating": aesthetic_rating,
            "production_ready": False,
            "lifecycle_state": "reviewed",
            "visual_review": copy.deepcopy(visual_review),
            "original_quality": "reviewed",
            "analysis_quality": "reviewed" if ref.metadata.get("figure_card_path") else "unassessed",
            "reconstruction_fidelity": (
                "reviewed" if ref.metadata.get("reproduction_preview_path") else "not_applicable"
            ),
            "eligible_for_style": aesthetic_rating >= 3,
            "eligible_for_structure": aesthetic_rating >= 3 and bool(ref.metadata.get("figure_card_path")),
            "eligible_for_reconstruction": bool(ref.metadata.get("code_path")),
            # Code reuse is a stronger claim than having runnable code.  It is
            # enabled only by an explicit fidelity verdict in visual_review.
            "eligible_for_code_reuse": visual_review.get("reconstruction_fidelity") == "pass",
        })
        quarantine = ref.metadata.get("quarantine") if isinstance(ref.metadata.get("quarantine"), dict) else {"history": []}
        history = list(quarantine.get("history") or [])
        history.append({"state": "reviewed", "reviewer": visual_review.get("reviewer")})
        ref.metadata["quarantine"] = {"state": "reviewed", "history": history}
        meta_path = self._metadata_path(ref.id, ref.scope)
        meta_path.write_text(
            json.dumps(ref.metadata, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self._refs[ref.id] = ref
        return ref

    def benchmark_reference(self, ref_id: str, canary_report: Dict[str, Any]) -> VisualReference:
        """Move a reviewed reference into the formal retrieval pool.

        A successful retrieval and generation canary is required; merely having
        a runnable renderer or a human review cannot bypass this gate.
        """
        ref = self.get(ref_id)
        if ref is None:
            raise KeyError(f"Unknown visual reference: {ref_id}")
        if ref.metadata.get("review_status") not in {"reviewed", "promoted"}:
            raise ValueError("Reference must be reviewed before benchmarking.")
        if not isinstance(canary_report, dict) or canary_report.get("canary_pass") is not True:
            raise ValueError("A passing retrieval and generation canary is required.")
        history = list((ref.metadata.get("quarantine") or {}).get("history") or [])
        history.append({"state": "benchmarked", "report": copy.deepcopy(canary_report)})
        ref.metadata["lifecycle_state"] = "benchmarked"
        ref.metadata["quarantine"] = {"state": "benchmarked", "history": history}
        self._write_metadata(ref)
        return ref

    def promote_reference(self, ref_id: str, evidence: Dict[str, Any]) -> VisualReference:
        """Promote a benchmarked reference to the production recommendation pool."""
        ref = self.get(ref_id)
        if ref is None:
            raise KeyError(f"Unknown visual reference: {ref_id}")
        if ref.metadata.get("lifecycle_state") != "benchmarked":
            raise ValueError("Reference must be benchmarked before production promotion.")
        if not isinstance(evidence, dict) or evidence.get("champion_floor_pass") is not True:
            raise ValueError("Champion-floor evidence is required for promotion.")
        ref.metadata["lifecycle_state"] = "production"
        ref.metadata["production_ready"] = True
        history = list((ref.metadata.get("quarantine") or {}).get("history") or [])
        history.append({"state": "production", "evidence": copy.deepcopy(evidence)})
        ref.metadata["quarantine"] = {"state": "production", "history": history}
        self._write_metadata(ref)
        return ref

    def _write_metadata(self, ref: VisualReference) -> None:
        meta_path = self._metadata_path(ref.id, ref.scope)
        meta_path.write_text(
            json.dumps(ref.metadata, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def list(
        self,
        scope: Optional[str] = None,
        figure_type: Optional[str] = None,
        review_status: Optional[str] = None,
        production_ready: Optional[bool] = None,
    ) -> List[VisualReference]:
        """List references with optional simple filters."""
        results = []
        for ref in self.all():
            if scope is not None and ref.scope != scope:
                continue
            if figure_type is not None and ref.figure_type != normalize_figure_type(figure_type):
                continue
            if review_status is not None and ref.metadata.get("review_status") != review_status:
                continue
            if production_ready is not None and ref.metadata.get("production_ready") != production_ready:
                continue
            results.append(ref)
        return results

    def query(
        self,
        figure_type: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        palette: Optional[str] = None,
        journal_style: Optional[str] = None,
        layout: Optional[str] = None,
        n_groups: Optional[int] = None,
        data_density: Optional[str] = None,
        review_status: Optional[str] = None,
        usage_scope: Optional[str] = None,
        production_ready: Optional[bool] = None,
        min_aesthetic_rating: Optional[float] = None,
        include_unreviewed: bool = False,
        sort_by: Tuple[str, ...] = ("review_state", "aesthetic_desc", "tag_match", "created_desc"),
        limit: Optional[int] = None,
    ) -> List[VisualReference]:
        """Query references using metadata filters.

        Result eligibility and ranking (default):
        1. exclude pending/rejected; promoted entries before reviewed
        2. higher aesthetic_rating first
        3. more tag matches first
        4. newer entries first
        """
        tags = set(t.lower().strip() for t in (tags or []))

        scored = []
        for ref in self.all():
            m = ref.metadata
            if figure_type is not None and normalize_figure_type(m.get("figure_type", "")) != normalize_figure_type(figure_type):
                continue
            if review_status is None and not include_unreviewed and m.get("review_status") not in {"reviewed", "promoted"}:
                continue
            # ``query`` is also the diagnostic/audit API, so reviewed records
            # remain visible here.  Formal recommendation uses the stricter
            # benchmarked/production filter below.
            if not include_unreviewed and m.get("lifecycle_state") and m.get("lifecycle_state") in {"raw", "analyzed", "rejected"} and m.get("review_status") not in {"reviewed", "promoted"}:
                continue
            if m.get("reference_kind") == "exact_visual_source" and m.get("review_status") != "reviewed":
                continue
            if palette is not None and m.get("palette") != palette:
                continue
            if journal_style is not None and m.get("journal_style") != journal_style:
                continue
            if layout is not None and m.get("layout") != layout:
                continue
            if data_density is not None and m.get("data_density") != data_density:
                continue
            if review_status is not None and m.get("review_status") != review_status:
                continue
            if usage_scope is not None and m.get("usage_scope") != usage_scope:
                continue
            if production_ready is not None and m.get("production_ready") != production_ready:
                continue
            if n_groups is not None and m.get("n_groups") != n_groups:
                continue
            if min_aesthetic_rating is not None:
                r = m.get("aesthetic_rating")
                if r is None or r < min_aesthetic_rating:
                    continue

            ref_tags = set(t.lower().strip() for t in m.get("tags", []))
            tag_hits = len(tags & ref_tags) if tags else 0

            score = {
                "review_state": {"promoted": 0, "reviewed": 1}.get(m.get("review_status"), 2),
                "reviewed_first": 0 if m.get("review_status") in {"reviewed", "promoted"} else 1,
                "aesthetic_desc": -(m.get("aesthetic_rating") or 0),
                "tag_match": -tag_hits,
                "created_desc": -(datetime.strptime(m["created_at"], _UTC_FMT).timestamp() if m.get("created_at") else 0),
            }

            sort_key = tuple(score.get(k, 0) for k in sort_by)
            scored.append((sort_key, ref))

        scored.sort(key=lambda x: x[0])
        refs = [r for _, r in scored]
        if limit is not None:
            refs = refs[:limit]
        return refs

    def recommend_candidates(
        self,
        figure_type: str,
        *,
        required_tags: Optional[Iterable[str]] = None,
        preferred_tags: Optional[Iterable[str]] = None,
        layout: Optional[str] = None,
        data_density: Optional[str] = None,
        n_groups: Optional[int] = None,
        journal_style: Optional[str] = None,
        exclude_ids: Optional[Iterable[str]] = None,
        limit: int = 3,
        require_benchmark: bool = False,
    ) -> Dict[str, Any]:
        """Recommend an explainable, task-compatible, diverse visual shortlist."""
        canonical_type = normalize_figure_type(figure_type)
        if not canonical_type:
            raise ValueError("figure_type is required for candidate recommendation.")
        if limit < 1 or limit > 3:
            raise ValueError("limit must be between 1 and 3.")
        required = {str(tag).strip().lower() for tag in (required_tags or []) if str(tag).strip()}
        preferred = {str(tag).strip().lower() for tag in (preferred_tags or []) if str(tag).strip()}
        excluded = {str(ref_id).strip() for ref_id in (exclude_ids or []) if str(ref_id).strip()}

        type_pool = [
            ref for ref in self.all()
            if ref.id not in excluded
            and ref.metadata.get("review_status") in {"reviewed", "promoted"}
            and (
                ref.metadata.get("lifecycle_state", "benchmarked") in {"benchmarked", "production"}
                if require_benchmark
                else ref.metadata.get("review_status") in {"reviewed", "promoted"}
            )
            and ref.image_path is not None
            and ref.image_path.is_file()
            and not (
                ref.metadata.get("reference_kind") == "exact_visual_source"
                and ref.metadata.get("review_status") != "reviewed"
            )
            and normalize_figure_type(ref.figure_type) == canonical_type
        ]
        eligible = []
        for ref in type_pool:
            metadata = ref.metadata
            ref_tags = {str(tag).strip().lower() for tag in metadata.get("tags", [])}
            if not required.issubset(ref_tags):
                continue
            matches = ["Exact figure type"]
            cautions = []
            task_score = 0
            preferred_hits = sorted(preferred & ref_tags)
            if preferred:
                if preferred_hits:
                    task_score += 2 * len(preferred_hits)
                    matches.append("Preferred tags: " + ", ".join(preferred_hits))
                else:
                    cautions.append("No preferred tag match")
            for field, requested, weight, label in (
                ("layout", layout, 4, "Layout"),
                ("data_density", data_density, 3, "Data density"),
                ("n_groups", n_groups, 2, "Group count"),
                ("journal_style", journal_style, 2, "Journal style"),
            ):
                if requested is None:
                    continue
                actual = metadata.get(field)
                if str(actual).lower() == str(requested).lower():
                    task_score += weight
                    matches.append(f"{label}: {requested}")
                else:
                    cautions.append(f"{label} mismatch: requested {requested}, candidate {actual}")
            source_family = (
                metadata.get("source_repository")
                or metadata.get("source")
                or metadata.get("scope")
                or "unknown"
            )
            eligible.append({
                "ref": ref,
                "task_score": task_score,
                "rating": float(metadata.get("aesthetic_rating") or 0),
                "matches": matches,
                "cautions": cautions,
                "subtype": metadata.get("subtype") or canonical_type,
                "layout": metadata.get("layout") or "unknown",
                "source_family": str(source_family),
                "content_sha256": _sha256_of_bytes(ref.image_path.read_bytes()),
            })

        # Metadata can be copied or hand-edited while pointing at the same
        # pixels. Keep the strongest eligible record only; otherwise a
        # three-item shortlist can silently return the same image three times.
        eligible.sort(key=lambda item: (-item["task_score"], -item["rating"], item["ref"].id))
        unique_eligible = []
        seen_content = set()
        for item in eligible:
            if item["content_sha256"] in seen_content:
                continue
            seen_content.add(item["content_sha256"])
            unique_eligible.append(item)
        eligible = unique_eligible

        selected = []
        remaining = list(eligible)
        while remaining and len(selected) < limit:
            used_subtypes = {item["subtype"] for item in selected}
            used_layouts = {item["layout"] for item in selected}
            used_sources = {item["source_family"] for item in selected}
            for item in remaining:
                diversity_score = 0
                diversity_reasons = []
                if selected and item["subtype"] not in used_subtypes:
                    diversity_score += 2
                    diversity_reasons.append("different subtype")
                if selected and item["layout"] not in used_layouts:
                    diversity_score += 1
                    diversity_reasons.append("different layout")
                if selected and item["source_family"] not in used_sources:
                    diversity_score += 1
                    diversity_reasons.append("different source family")
                item["diversity_score"] = diversity_score
                item["diversity_reasons"] = diversity_reasons
                item["selection_score"] = item["task_score"] * 10 + diversity_score * 2 + item["rating"]
            remaining.sort(
                key=lambda item: (
                    -item["selection_score"],
                    0 if item["ref"].metadata.get("review_status") == "promoted" else 1,
                    item["ref"].id,
                )
            )
            chosen = remaining.pop(0)
            selected.append(chosen)

        candidates = []
        for rank, item in enumerate(selected, start=1):
            ref = item["ref"]
            candidates.append({
                "rank": rank,
                "id": ref.id,
                "image_path": ref.metadata.get("image_path"),
                # Recompute from the candidate pixels rather than trusting a
                # hand-edited sidecar field; downstream reference provenance
                # compares this digest with the opened image bytes.
                "image_sha256": item["content_sha256"],
                "figure_type": ref.figure_type,
                "subtype": ref.metadata.get("subtype"),
                "layout": ref.metadata.get("layout"),
                "source_family": item["source_family"],
                "review_status": ref.metadata.get("review_status"),
                "aesthetic_rating": ref.metadata.get("aesthetic_rating"),
                "task_score": item["task_score"],
                "diversity_score": item["diversity_score"],
                "selection_score": round(item["selection_score"], 3),
                "matches": item["matches"],
                "cautions": item["cautions"],
                "diversity_reasons": item["diversity_reasons"],
            })
        insufficient = len(candidates) < limit
        return {
            "status": "insufficient_pool" if insufficient else "ready",
            "insufficient_pool": insufficient,
            "requested_limit": limit,
            "request": {
                "figure_type": canonical_type,
                "required_tags": sorted(required),
                "preferred_tags": sorted(preferred),
                "layout": layout,
                "data_density": data_density,
                "n_groups": n_groups,
                "journal_style": journal_style,
                "exclude_ids": sorted(excluded),
            },
            "pool": {
                "exact_type_reviewed": len(type_pool),
                "after_required_tags": len(eligible),
                "returned": len(candidates),
            },
            "candidates": candidates,
        }

    def all(self) -> List[VisualReference]:
        """Load and return every reference found on disk."""
        refs: List[VisualReference] = []
        for scope in _SCOPES:
            scope_dir = self._visual_refs_dir() / scope
            if not scope_dir.exists():
                continue
            for asset_dir in sorted(scope_dir.iterdir()):
                if not asset_dir.is_dir():
                    continue
                meta_path = asset_dir / "metadata.json"
                if not meta_path.exists():
                    continue
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                ref = VisualReference(meta, self.root)
                self._refs[ref.id] = ref
                refs.append(ref)
        return refs

    def resolve_visual_style(
        self,
        figure_type: str,
        reference_id: Optional[str] = None,
        user_colors: Optional[Sequence[str]] = None,
        user_palette: Optional[str] = None,
        n: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Resolve colors and palette provenance for a new generated panel.

        Priority (highest first):
        1. ``user_colors`` — explicit user-supplied colors are returned as-is.
        2. ``user_palette`` — explicit user palette id / Chinese alias.
        3. Visual reference original palette (``reference_id``):
           - ``palette_policy = preserve`` → use the reference palette as-is.
           - ``palette_policy = adaptable`` → resolve through ``palette_manager``
             so the palette can be adjusted or extended.
        4. Skill default palette.

        Native-run production assets are NOT passed through this function; their
        hard-coded colors are preserved as visual snapshots.

        Returns
        -------
        dict
            {
                "colors": [...],
                "palette": palette_id or None,
                "palette_policy": "preserve" | "adaptable" | None,
                "source": "user_colors" | "user_palette" | "reference" | "default",
            }
        """
        try:
            from .palette_manager import resolve_colors, resolve_palette
        except ImportError:  # pragma: no cover - allow standalone import during dev
            from palette_manager import resolve_colors, resolve_palette

        # Validate an explicitly supplied reference even when an explicit
        # palette/color list wins precedence.  Otherwise a typo or a
        # cross-type reference would be silently ignored and the caller could
        # believe the requested visual source was used.
        ref = None
        if reference_id:
            ref = self.get(reference_id)
            if ref is None:
                raise ValueError(f"Unknown visual reference: {reference_id}")
            requested_type = normalize_figure_type(figure_type)
            if ref.figure_type != requested_type:
                raise ValueError(
                    f"Reference {reference_id} has figure type {ref.figure_type}, "
                    f"not compatible with requested {requested_type}."
                )

        # 1. User explicit colors win.
        if user_colors is not None and len(user_colors) > 0:
            return {
                "colors": list(user_colors),
                "palette": None,
                "palette_policy": None,
                "source": "user_colors",
            }

        # 2. User explicit palette.
        if user_palette is not None:
            return {
                "colors": resolve_colors(palette=user_palette, n=n),
                "palette": user_palette,
                "palette_policy": "adaptable",  # user palette is adjustable
                "source": "user_palette",
            }

        # 3. Visual reference palette (only for new generated / adapted panels).
        if ref is not None and ref.metadata.get("palette") is not None:
            ref_palette = ref.metadata["palette"]
            policy = ref.metadata.get("palette_policy", "preserve")
            if policy == "preserve":
                return {
                    "colors": resolve_colors(palette=ref_palette, n=n),
                    "palette": ref_palette,
                    "palette_policy": "preserve",
                    "source": "reference",
                }
            # adaptable: resolve through palette manager so it can extend/adjust.
            return {
                "colors": resolve_colors(palette=ref_palette, n=n),
                "palette": ref_palette,
                "palette_policy": "adaptable",
                "source": "reference",
            }

        # 4. Skill default palette.
        return {
            "colors": resolve_palette(n=n),
            "palette": None,
            "palette_policy": None,
            "source": "default",
        }

    def validate(self) -> Tuple[bool, List[Tuple[str, List[str]]]]:
        """Validate every side-car metadata file."""
        problems: List[Tuple[str, List[str]]] = []
        all_ok = True
        for ref in self.all():
            ok, errors = validate_metadata(ref.metadata, root=self.root)
            image_path = ref.image_path
            if image_path is None or not image_path.is_file():
                ok = False
                errors.append("image file is missing")
            else:
                try:
                    actual_sha256 = _sha256_of_bytes(image_path.read_bytes())
                except OSError as exc:
                    ok = False
                    errors.append(f"image file is unreadable: {exc}")
                else:
                    expected_sha256 = ref.metadata.get("sha256")
                    if not expected_sha256:
                        ok = False
                        errors.append("sha256 is missing")
                    elif actual_sha256 != expected_sha256:
                        ok = False
                        errors.append("sha256 does not match image pixels")
                for derivative_key in ("preview_path", "thumbnail_path"):
                    derivative = ref.metadata.get(derivative_key)
                    if derivative and not (self.root / derivative).is_file():
                        ok = False
                        errors.append(f"{derivative_key} file is missing")
            if not ok:
                all_ok = False
                problems.append((ref.id, errors))
        return all_ok, problems

    def rebuild_registry(self) -> Path:
        """Rebuild ``registry.jsonl`` from side-car metadata files."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with self.registry_path.open("w", encoding="utf-8") as fh:
            for ref in self.all():
                fh.write(json.dumps(ref.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        self._refs.clear()
        return self.registry_path

    def load_registry(self) -> List[VisualReference]:
        """Load references from ``registry.jsonl`` if present."""
        refs: List[VisualReference] = []
        if not self.registry_path.exists():
            return refs
        with self.registry_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                meta = json.loads(line)
                ref = VisualReference(meta, self.root)
                refs.append(ref)
                self._refs[ref.id] = ref
        return refs


# ---------------------------------------------------------------------------
# Convenience module-level helpers
# ---------------------------------------------------------------------------

def ingest_image(
    image_path: Path,
    figure_type: str,
    metadata_override: Optional[Dict[str, Any]] = None,
    copy: bool = True,
) -> VisualReference:
    """Module-level helper to ingest an external image."""
    lib = ReferenceLibrary()
    return lib.ingest(
        image_path=image_path,
        figure_type=figure_type,
        scope="references",
        metadata_override=metadata_override,
        copy=copy,
    )


def archive_generated_figure(
    image_path: Path,
    figure_type: str,
    code_path: Optional[Path] = None,
    metadata_override: Optional[Dict[str, Any]] = None,
    copy: bool = True,
) -> VisualReference:
    """Module-level helper to archive a self-generated figure."""
    lib = ReferenceLibrary()
    return lib.archive_generated_figure(
        image_path=image_path,
        figure_type=figure_type,
        code_path=code_path,
        metadata_override=metadata_override,
        copy=copy,
    )


def resolve_visual_style(
    figure_type: str,
    reference_id: Optional[str] = None,
    user_colors: Optional[Sequence[str]] = None,
    user_palette: Optional[str] = None,
    n: Optional[int] = None,
) -> Dict[str, Any]:
    """Module-level helper to resolve colors for a new generated panel."""
    return ReferenceLibrary().resolve_visual_style(
        figure_type=figure_type,
        reference_id=reference_id,
        user_colors=user_colors,
        user_palette=user_palette,
        n=n,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _pretty_print(ref: VisualReference) -> None:
    print(ref.to_json(indent=2))
    print()


def cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Visual Reference Library manager for publication-figure-design."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ingest
    ingest_p = sub.add_parser("ingest", help="Ingest an external image as a visual reference.")
    ingest_p.add_argument("image", type=Path, help="Path to the source image.")
    ingest_p.add_argument("figure_type", help="Figure type, e.g. GroupedViolin.")
    ingest_p.add_argument("--metadata", "-m", type=str, default="{}",
                          help="JSON string of extra metadata fields.")
    ingest_p.add_argument("--move", action="store_true",
                          help="Move the image instead of copying.")
    ingest_p.add_argument("--scope", default="references", choices=sorted(_SCOPES))

    # archive
    archive_p = sub.add_parser("archive", help="Archive a self-generated figure.")
    archive_p.add_argument("image", type=Path)
    archive_p.add_argument("figure_type")
    archive_p.add_argument("--code", type=Path, default=None)
    archive_p.add_argument("--metadata", "-m", type=str, default="{}")
    archive_p.add_argument("--move", action="store_true")

    # list
    list_p = sub.add_parser("list", help="List references.")
    list_p.add_argument("--scope", choices=sorted(_SCOPES))
    list_p.add_argument("--figure-type")
    list_p.add_argument("--review-status", choices=sorted(_REVIEW_STATUSES))
    list_p.add_argument("--production-ready", type=lambda x: x.lower() == "true")

    # get
    get_p = sub.add_parser("get", help="Get one reference by id.")
    get_p.add_argument("id")

    # query
    query_p = sub.add_parser("query", help="Query references by metadata filters.")
    query_p.add_argument("--figure-type")
    query_p.add_argument("--tags", type=str, default="",
                         help="Comma-separated tags.")
    query_p.add_argument("--palette")
    query_p.add_argument("--journal-style")
    query_p.add_argument("--layout")
    query_p.add_argument("--data-density")
    query_p.add_argument("--review-status")
    query_p.add_argument("--min-aesthetic-rating", type=float)
    query_p.add_argument("--limit", type=int)

    # recommend (strict task-specific shortlist)
    recommend_p = sub.add_parser("recommend", help="Recommend task-compatible diverse candidates.")
    recommend_p.add_argument("--figure-type", required=True)
    recommend_p.add_argument("--required-tags", default="")
    recommend_p.add_argument("--preferred-tags", default="")
    recommend_p.add_argument("--layout")
    recommend_p.add_argument("--data-density")
    recommend_p.add_argument("--n-groups", type=int)
    recommend_p.add_argument("--journal-style")
    recommend_p.add_argument("--exclude-ids", default="")
    recommend_p.add_argument("--limit", type=int, default=3)
    recommend_p.add_argument("--require-benchmark", action="store_true")
    recommend_p.add_argument("--json", dest="json_path", type=Path)
    recommend_p.add_argument("--root", type=Path, help=argparse.SUPPRESS)

    # validate
    sub.add_parser("validate", help="Validate all side-car metadata files.")

    # rebuild
    sub.add_parser("rebuild", help="Rebuild registry.jsonl from side-car metadata.")

    args = parser.parse_args(argv)
    lib = ReferenceLibrary(root=args.root) if args.command == "recommend" and args.root else ReferenceLibrary()

    if args.command == "ingest":
        meta_override = json.loads(args.metadata)
        ref = lib.ingest(
            image_path=args.image,
            figure_type=args.figure_type,
            scope=args.scope,
            metadata_override=meta_override,
            copy=not args.move,
        )
        print(f"Ingested {ref.id}: {ref.metadata['image_path']}")
        return 0

    if args.command == "archive":
        meta_override = json.loads(args.metadata)
        ref = lib.archive_generated_figure(
            image_path=args.image,
            figure_type=args.figure_type,
            code_path=args.code,
            metadata_override=meta_override,
            copy=not args.move,
        )
        print(f"Archived {ref.id}: {ref.metadata['image_path']}")
        return 0

    if args.command == "list":
        refs = lib.list(
            scope=args.scope,
            figure_type=args.figure_type,
            review_status=args.review_status,
            production_ready=args.production_ready,
        )
        print(f"Found {len(refs)} reference(s)")
        for ref in refs:
            _pretty_print(ref)
        return 0

    if args.command == "get":
        ref = lib.get(args.id)
        if ref is None:
            print(f"Reference {args.id!r} not found.", file=sys.stderr)
            return 1
        _pretty_print(ref)
        return 0

    if args.command == "query":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None
        refs = lib.query(
            figure_type=args.figure_type,
            tags=tags,
            palette=args.palette,
            journal_style=args.journal_style,
            layout=args.layout,
            data_density=args.data_density,
            review_status=args.review_status,
            min_aesthetic_rating=args.min_aesthetic_rating,
            limit=args.limit,
        )
        print(f"Found {len(refs)} reference(s)")
        for ref in refs:
            _pretty_print(ref)
        return 0

    if args.command == "recommend":
        split = lambda value: [part.strip() for part in value.split(",") if part.strip()]
        report = lib.recommend_candidates(
            figure_type=args.figure_type,
            required_tags=split(args.required_tags),
            preferred_tags=split(args.preferred_tags),
            layout=args.layout,
            data_density=args.data_density,
            n_groups=args.n_groups,
            journal_style=args.journal_style,
            exclude_ids=split(args.exclude_ids),
            limit=args.limit,
            require_benchmark=args.require_benchmark,
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if args.json_path:
            args.json_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        return 0

    if args.command == "validate":
        ok, problems = lib.validate()
        if ok:
            print("All references are valid.")
            return 0
        for ref_id, errors in problems:
            print(f"{ref_id}: {'; '.join(errors)}")
        return 1

    if args.command == "rebuild":
        path = lib.rebuild_registry()
        print(f"Rebuilt registry: {path}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(cli())
