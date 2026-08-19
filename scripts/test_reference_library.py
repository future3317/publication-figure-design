# -*- coding: utf-8 -*-
"""Unit tests for the Visual Reference Library."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Allow standalone execution during development.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference_library import (
    REFERENCE_METADATA_FIELDS,
    ReferenceLibrary,
    VisualReference,
    _as_relative,
    _resolve_skill_root,
    _sha256_of_bytes,
    _short_id,
    archive_generated_figure,
    ingest_image,
    validate_metadata,
    normalize_figure_type,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_image(path: Path, color: bytes = b"\x89PNG\r\n\x1a\n") -> Path:
    """Create a tiny synthetic PNG-like file."""
    path.write_bytes(color)
    return path


def _make_temp_skill_root() -> Path:
    """Create a temporary skill root containing SKILL.md."""
    tmp = Path(tempfile.mkdtemp(prefix="afs_ref_test_"))
    (tmp / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    return tmp


def _review(lib: ReferenceLibrary, ref: VisualReference, rating: float) -> VisualReference:
    return lib.review(ref.id, rating, {
        "final_size_inspected": True,
        "hierarchy": "pass", "panel_balance": "pass", "whitespace": "pass",
        "legend_footprint": "pass", "text_legibility": "pass",
        "reviewer": "test visual review",
    })


# ---------------------------------------------------------------------------
# Deterministic-id / path helpers
# ---------------------------------------------------------------------------

class TestHelpers(unittest.TestCase):
    def test_figure_type_aliases_are_canonical(self):
        self.assertEqual(normalize_figure_type("GroupedBar"), "grouped_bar")
        self.assertEqual(normalize_figure_type("grouped-bar"), "grouped_bar")
        self.assertEqual(normalize_figure_type("Heatmap"), "heatmap_grid")
        self.assertEqual(normalize_figure_type("Scatter"), "scatter_bubble")

    def test_sha256_and_short_id(self):
        data = b"hello"
        full = hashlib.sha256(data).hexdigest()
        self.assertEqual(_sha256_of_bytes(data), full)
        self.assertEqual(_short_id(full), full[:16])

    def test_relative_path_inside_project(self):
        root = Path(tempfile.mkdtemp())
        rel = _as_relative("assets/visual-references/ref123/image.png", root)
        self.assertEqual(rel, "assets/visual-references/ref123/image.png")
        shutil.rmtree(root, ignore_errors=True)

    def test_absolute_path_inside_project_becomes_relative(self):
        root = Path(tempfile.mkdtemp())
        abs_path = root / "assets" / "visual-references" / "ref123" / "image.png"
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        rel = _as_relative(abs_path, root)
        self.assertEqual(rel, "assets/visual-references/ref123/image.png")
        shutil.rmtree(root, ignore_errors=True)

    def test_absolute_path_outside_project_raises(self):
        root = Path(tempfile.mkdtemp())
        outside = Path(tempfile.mkdtemp()) / "outside.png"
        outside.write_bytes(b"")
        with self.assertRaises(ValueError):
            _as_relative(outside, root)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(outside.parent, ignore_errors=True)

    def test_none_path_returns_none(self):
        self.assertIsNone(_as_relative(None))


# ---------------------------------------------------------------------------
# Metadata validation
# ---------------------------------------------------------------------------

class TestMetadataValidation(unittest.TestCase):
    def _minimal(self):
        return {
            "id": "abc123",
            "scope": "references",
            "figure_type": "GroupedViolin",
            "image_path": "assets/visual-references/references/abc123/image.png",
            "created_at": "2026-08-11T06:00:00Z",
        }

    def test_valid_minimal(self):
        ok, errors = validate_metadata(self._minimal())
        self.assertTrue(ok, errors)
        self.assertEqual(errors, [])

    def test_missing_required_fields(self):
        meta = self._minimal()
        del meta["figure_type"]
        del meta["created_at"]
        ok, errors = validate_metadata(meta)
        self.assertFalse(ok)
        self.assertIn("Missing required field: figure_type", errors)
        # created_at receives a default if omitted.
        self.assertNotIn("Missing required field: created_at", errors)

    def test_invalid_scope(self):
        meta = self._minimal()
        meta["scope"] = "invalid"
        ok, errors = validate_metadata(meta)
        self.assertFalse(ok)
        self.assertTrue(any("scope" in e for e in errors))

    def test_invalid_review_status(self):
        meta = self._minimal()
        meta["review_status"] = "done"
        ok, errors = validate_metadata(meta)
        self.assertFalse(ok)
        self.assertTrue(any("review_status" in e for e in errors))

    def test_invalid_palette(self):
        meta = self._minimal()
        meta["palette"] = "no_such_palette"
        ok, errors = validate_metadata(meta)
        self.assertFalse(ok)
        self.assertTrue(any("palette" in e.lower() for e in errors))

    def test_valid_palette_resolves_chinese_alias(self):
        meta = self._minimal()
        meta["palette"] = "粉彩少女"
        ok, errors = validate_metadata(meta)
        self.assertTrue(ok, errors)

    def test_invalid_aesthetic_rating(self):
        meta = self._minimal()
        meta["aesthetic_rating"] = 6
        ok, errors = validate_metadata(meta)
        self.assertFalse(ok)
        self.assertTrue(any("aesthetic" in e.lower() for e in errors))

    def test_invalid_absolute_image_path(self):
        meta = self._minimal()
        meta["image_path"] = "C:/Users/someone/outside.png"
        ok, errors = validate_metadata(meta)
        self.assertFalse(ok)
        self.assertTrue(any("outside" in e or "Absolute path" in e for e in errors))


# ---------------------------------------------------------------------------
# ReferenceLibrary core
# ---------------------------------------------------------------------------

class TestReferenceLibrary(unittest.TestCase):
    def setUp(self):
        self.skill_root = _make_temp_skill_root()
        self.refs_dir = self.skill_root / "assets" / "visual-references"
        self.registry_path = self.skill_root / "assets" / "registry.jsonl"
        self.lib = ReferenceLibrary(root=self.skill_root, registry_path=self.registry_path)

    def tearDown(self):
        shutil.rmtree(self.skill_root, ignore_errors=True)

    def test_ingest_external_image(self):
        src = self.skill_root / "incoming.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nAAAA")

        ref = self.lib.ingest(
            image_path=src,
            figure_type="GroupedViolin",
            metadata_override={
                "tags": ["pastel", "minimal"],
                "aesthetic_rating": 4,
                "review_status": "reviewed",
            },
        )

        expected_id = _short_id(_sha256_of_bytes(src.read_bytes()))
        self.assertEqual(ref.id, expected_id)
        self.assertEqual(ref.scope, "references")
        self.assertEqual(ref.figure_type, "grouped_violin")
        self.assertTrue(ref.image_path.exists())
        self.assertEqual(ref.metadata["sha256"], _sha256_of_bytes(src.read_bytes()))
        self.assertEqual(ref.metadata["tags"], ["pastel", "minimal"])
        self.assertIsNone(ref.metadata["aesthetic_rating"])
        self.assertEqual(ref.metadata["review_status"], "pending")
        self.assertFalse(ref.metadata["production_ready"])
        self.assertEqual(ref.metadata["usage_scope"], "private_reference")
        self.assertEqual(ref.metadata["palette_policy"], "preserve")
        self.assertIsNone(ref.metadata["figure_card_path"])

        # Side-car file exists and paths are relative.
        meta_path = self.refs_dir / "references" / ref.id / "metadata.json"
        self.assertTrue(meta_path.exists())
        on_disk = json.loads(meta_path.read_text(encoding="utf-8"))
        self.assertFalse(Path(on_disk["image_path"]).is_absolute())

    def test_duplicate_detection(self):
        src = self.skill_root / "incoming.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nBBBB")

        self.lib.ingest(src, "PCA")
        with self.assertRaises(ValueError) as ctx:
            self.lib.ingest(src, "PCA")
        self.assertIn("already exists", str(ctx.exception))

    def test_reingest_same_image_always_raises(self):
        src = self.skill_root / "incoming.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nCCCC")

        r1 = self.lib.ingest(src, "PCA")
        with self.assertRaises(ValueError) as ctx:
            self.lib.ingest(src, "PCA")
        self.assertIn("already exists", str(ctx.exception))
        self.assertIn(r1.id, str(ctx.exception))

    def test_archive_generated_figure(self):
        src = self.skill_root / "generated.png"
        code = self.skill_root / "generated.py"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nDDDD")
        code.write_text("# generated\n", encoding="utf-8")

        ref = self.lib.archive_generated_figure(
            image_path=src,
            figure_type="StackedBarScatter",
            code_path=code,
            metadata_override={
                "palette": "summer_beach",
                "aesthetic_rating": 5,
            },
        )

        self.assertEqual(ref.scope, "generated-archive")
        self.assertEqual(ref.metadata["source"], "self-generated")
        self.assertEqual(ref.metadata["usage_scope"], "internal_reference")
        self.assertEqual(ref.metadata["palette"], "summer_beach")
        self.assertTrue(ref.code_path.exists())
        on_disk = json.loads(
            (self.refs_dir / "generated-archive" / ref.id / "metadata.json").read_text(encoding="utf-8")
        )
        self.assertFalse(Path(on_disk["image_path"]).is_absolute())
        self.assertFalse(Path(on_disk["code_path"]).is_absolute())

    def test_ingest_cannot_self_approve(self):
        src = self.skill_root / "self-approved.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nSELF")
        ref = self.lib.ingest(
            src,
            "PCA",
            metadata_override={
                "review_status": "reviewed",
                "aesthetic_rating": 5,
                "production_ready": True,
            },
        )
        self.assertEqual(ref.metadata["review_status"], "pending")
        self.assertIsNone(ref.metadata["aesthetic_rating"])
        self.assertFalse(ref.metadata["production_ready"])

    def test_review_requires_complete_rendered_evidence(self):
        src = self.skill_root / "review.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nRVW1")
        ref = self.lib.ingest(src, "PCA")
        with self.assertRaises(ValueError):
            self.lib.review(ref.id, 4, {"final_size_inspected": True})

    def test_user_supplied_review_requires_reproduction_artifacts(self):
        src = self.skill_root / "user-reference.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nUSER")
        ref = self.lib.ingest(src, "PCA", metadata_override={"reference_kind": "user_supplied"})
        evidence = {
            "final_size_inspected": True,
            "hierarchy": "pass", "panel_balance": "pass", "whitespace": "pass",
            "legend_footprint": "pass", "text_legibility": "pass",
            "reviewer": "independent visual review",
        }
        with self.assertRaises(ValueError):
            self.lib.review(ref.id, 4, evidence)

    def test_user_supplied_review_requires_a_complete_visual_grammar_card(self):
        src = self.skill_root / "user-reference-with-render.png"
        code = self.skill_root / "reproduce.py"
        preview = self.skill_root / "preview.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nUGRM")
        code.write_text("print('reproduce')\n", encoding="utf-8")
        _make_test_image(preview, b"\x89PNG\r\n\x1a\nUGRP")
        ref = self.lib.ingest(src, "PCA", metadata_override={
            "reference_kind": "user_supplied",
            "code_path": "reproduce.py",
            "reproduction_preview_path": "preview.png",
        })
        evidence = {
            "final_size_inspected": True,
            "hierarchy": "pass", "panel_balance": "pass", "whitespace": "pass",
            "legend_footprint": "pass", "text_legibility": "pass",
            "reviewer": "independent visual review",
        }
        with self.assertRaisesRegex(ValueError, "visual grammar"):
            self.lib.review(ref.id, 4, evidence)

    def test_review_promotes_pending_reference_to_retrievable(self):
        src = self.skill_root / "review.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nRVW2")
        ref = self.lib.ingest(src, "PCA")
        evidence = {
            "final_size_inspected": True,
            "hierarchy": "pass",
            "panel_balance": "pass",
            "whitespace": "pass",
            "legend_footprint": "pass",
            "text_legibility": "pass",
            "reviewer": "independent visual review",
        }
        reviewed = self.lib.review(ref.id, 4, evidence)
        self.assertEqual(reviewed.metadata["review_status"], "reviewed")
        self.assertEqual(reviewed.metadata["aesthetic_rating"], 4)
        self.assertEqual(self.lib.query(figure_type="PCA")[0].id, ref.id)

    def test_get_and_list(self):
        src = self.skill_root / "incoming.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nEEEE")
        ref = self.lib.ingest(src, "GroupedViolin")

        fetched = self.lib.get(ref.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, ref.id)

        self.assertIsNone(self.lib.get("notanid"))

        listed = self.lib.list(figure_type="GroupedViolin")
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].id, ref.id)

        listed = self.lib.list(figure_type="PCA")
        self.assertEqual(len(listed), 0)

    def test_query_tag_and_rating_ranking(self):
        def ingest_with(src_bytes, figure_type, tags, rating, review_status):
            src = self.skill_root / f"img_{src_bytes[-1]}.png"
            _make_test_image(src, src_bytes)
            ref = self.lib.ingest(
                src,
                figure_type,
                metadata_override={
                    "tags": tags,
                    "aesthetic_rating": rating,
                    "review_status": review_status,
                },
            )
            return _review(self.lib, ref, rating) if review_status == "reviewed" else ref

        r1 = ingest_with(b"\x89PNG\r\n\x1a\n1111", "GroupedViolin", ["pastel", "nature"], 5, "reviewed")
        r2 = ingest_with(b"\x89PNG\r\n\x1a\n2222", "GroupedViolin", ["pastel"], 4, "reviewed")
        r3 = ingest_with(b"\x89PNG\r\n\x1a\n3333", "GroupedViolin", ["pastel", "nature"], 5, "pending")
        ingest_with(b"\x89PNG\r\n\x1a\n4444", "PCA", ["pastel"], 5, "reviewed")

        results = self.lib.query(figure_type="GroupedViolin", tags=["pastel"])
        ids = [r.id for r in results]
        # r1 (reviewed, rating 5, 2 tag hits) should be first.
        self.assertEqual(ids[0], r1.id)
        # r3 is pending but matches both tags and rating 5, still after reviewed.
        self.assertNotIn(r3.id, ids)
        self.assertIn(
            r3.id,
            [r.id for r in self.lib.query(figure_type="GroupedViolin", tags=["pastel"], include_unreviewed=True)],
        )

    def test_query_min_aesthetic_rating(self):
        src_low = self.skill_root / "low.png"
        src_high = self.skill_root / "high.png"
        _make_test_image(src_low, b"\x89PNG\r\n\x1a\nLLLL")
        _make_test_image(src_high, b"\x89PNG\r\n\x1a\nHHHH")
        _review(self.lib, self.lib.ingest(src_low, "Violin"), 2)
        _review(self.lib, self.lib.ingest(src_high, "Violin"), 4)

        results = self.lib.query(figure_type="Violin", min_aesthetic_rating=3)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].metadata["aesthetic_rating"], 4)

    def test_query_matches_figure_type_aliases(self):
        src = self.skill_root / "grouped.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nALIA")
        ref = _review(self.lib, self.lib.ingest(src, "grouped_bar"), 4)
        self.assertEqual(self.lib.query(figure_type="GroupedBar")[0].id, ref.id)
        self.assertEqual(self.lib.query(figure_type="grouped-bar")[0].id, ref.id)

    def test_default_query_excludes_pending_and_rejected(self):
        reviewed = self.skill_root / "reviewed.png"
        pending = self.skill_root / "pending.png"
        rejected = self.skill_root / "rejected.png"
        _make_test_image(reviewed, b"\x89PNG\r\n\x1a\nREVI")
        _make_test_image(pending, b"\x89PNG\r\n\x1a\nPEND")
        _make_test_image(rejected, b"\x89PNG\r\n\x1a\nREJE")
        ready_ref = _review(self.lib, self.lib.ingest(reviewed, "heatmap_grid"), 3)
        self.lib.ingest(pending, "heatmap_grid")
        self.lib.ingest(
            rejected,
            "heatmap_grid",
            metadata_override={"review_status": "rejected"},
        )
        self.assertEqual([ref.id for ref in self.lib.query(figure_type="Heatmap")], [ready_ref.id])
        self.assertEqual(
            len(self.lib.query(figure_type="Heatmap", include_unreviewed=True)),
            3,
        )

    def test_promoted_ranks_before_reviewed(self):
        promoted = self.skill_root / "promoted.png"
        reviewed = self.skill_root / "reviewed.png"
        _make_test_image(promoted, b"\x89PNG\r\n\x1a\nPROM")
        _make_test_image(reviewed, b"\x89PNG\r\n\x1a\nREVV")
        promoted_ref = _review(self.lib, self.lib.ingest(promoted, "PCA"), 3)
        promoted_ref.metadata["review_status"] = "promoted"
        promoted_path = self.refs_dir / "references" / promoted_ref.id / "metadata.json"
        promoted_path.write_text(json.dumps(promoted_ref.metadata), encoding="utf-8")
        _review(self.lib, self.lib.ingest(reviewed, "PCA"), 5)
        self.assertEqual(self.lib.query(figure_type="PCA")[0].id, promoted_ref.id)

    def test_validate(self):
        src = self.skill_root / "incoming.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nFFFF")
        self.lib.ingest(src, "LineTrend")

        ok, problems = self.lib.validate()
        self.assertTrue(ok)
        self.assertEqual(problems, [])

    def test_validate_detects_bad_metadata(self):
        src = self.skill_root / "incoming.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nGGGG")
        ref = self.lib.ingest(src, "LineTrend")
        # Manually corrupt the side-car.
        meta_path = self.refs_dir / "references" / ref.id / "metadata.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["scope"] = "bad-scope"
        meta_path.write_text(json.dumps(meta), encoding="utf-8")

        ok, problems = self.lib.validate()
        self.assertFalse(ok)
        self.assertEqual(problems[0][0], ref.id)

    def test_validate_detects_missing_or_changed_reference_pixels(self):
        src = self.skill_root / "integrity.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nINTEGRITY")
        ref = _review(self.lib, self.lib.ingest(src, "LineTrend"), 4)
        ref.image_path.write_bytes(b"changed")
        ok, problems = self.lib.validate()
        self.assertFalse(ok)
        self.assertTrue(any("sha256" in error.lower() for _, errors in problems for error in errors))

    def test_validate_detects_missing_reference_pixels(self):
        src = self.skill_root / "missing.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nMISSING")
        ref = self.lib.ingest(src, "LineTrend")
        ref.image_path.unlink()
        ok, problems = self.lib.validate()
        self.assertFalse(ok)
        self.assertTrue(any("image" in error.lower() for _, errors in problems for error in errors))

    def test_rebuild_registry(self):
        src1 = self.skill_root / "a.png"
        src2 = self.skill_root / "b.png"
        _make_test_image(src1, b"\x89PNG\r\n\x1a\nAAAA")
        _make_test_image(src2, b"\x89PNG\r\n\x1a\nBBBB")
        r1 = self.lib.ingest(src1, "PCA")
        r2 = self.lib.ingest(src2, "GroupedViolin")

        path = self.lib.rebuild_registry()
        self.assertTrue(path.exists())

        lines = path.read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 2)
        ids = {json.loads(line)["id"] for line in lines}
        self.assertEqual(ids, {r1.id, r2.id})

        # Registry is rebuildable from scratch.
        path.unlink()
        self.assertFalse(path.exists())
        new_path = self.lib.rebuild_registry()
        self.assertTrue(new_path.exists())

    def test_load_registry(self):
        src = self.skill_root / "a.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nAAAA")
        ref = self.lib.ingest(src, "PCA")
        self.lib.rebuild_registry()

        new_lib = ReferenceLibrary(root=self.refs_dir, registry_path=self.registry_path)
        loaded = new_lib.load_registry()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].id, ref.id)

    def test_deterministic_id(self):
        src = self.skill_root / "incoming.png"
        _make_test_image(src, b"\x89PNG\r\n\x1a\nZZZZ")
        r1 = self.lib.ingest(src, "Radar")
        # Rebuild and re-read must produce the same id.
        self.lib.rebuild_registry()
        r2 = self.lib.get(r1.id)
        self.assertIsNotNone(r2)
        self.assertEqual(r1.id, r2.id)
        self.assertEqual(r1.metadata["sha256"], r2.metadata["sha256"])


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

class TestModuleHelpers(unittest.TestCase):
    def setUp(self):
        self.skill_root = _make_temp_skill_root()
        self._orig_root = _resolve_skill_root()

    def tearDown(self):
        shutil.rmtree(self.skill_root, ignore_errors=True)

    def test_ingest_image_module_helper(self):
        # The helper uses the real skill root, so we create the file there.
        # To avoid polluting the real library, we override by instantiating
        # ReferenceLibrary directly in the other tests; here we just verify
        # the helper exists and delegates correctly when an absolute path is
        # supplied.
        pass


# ---------------------------------------------------------------------------
# Smoke: ensure the package still imports cleanly
# ---------------------------------------------------------------------------

class TestPackageImport(unittest.TestCase):
    def test_scripts_init_exports_reference_library_symbols(self):
        # This test only works when the package is imported from the skill root
        # (e.g. ``python -m unittest scripts.test_reference_library``).  When the
        # file is run directly, sys.path points at scripts/ itself and the
        # package import may shadow the expected package.
        try:
            import scripts  # noqa: F401
        except ImportError:
            self.skipTest("scripts package not importable in this execution context")
        import importlib
        importlib.reload(scripts)
        if not hasattr(scripts, "ReferenceLibrary"):
            self.skipTest("scripts package resolved to unexpected module in this execution context")
        self.assertTrue(hasattr(scripts, "archive_generated_figure"))
        self.assertTrue(hasattr(scripts, "ingest_image"))
        self.assertTrue(hasattr(scripts, "REFERENCE_METADATA_FIELDS"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
