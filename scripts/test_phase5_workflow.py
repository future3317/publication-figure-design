# -*- coding: utf-8 -*-
"""Phase 5 real-task integration tests.

These tests verify that production asset metadata lets an agent quickly choose
the right implementation strategy, and that visual references only influence
visual language — never scientific semantics or figure type.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Allow standalone execution during development.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from production_asset_manager import ProductionAssetLibrary
from reference_library import ReferenceLibrary, resolve_visual_style


class TestProductionAssetMetadataGuidesCopyFirst(unittest.TestCase):
    """Verify metadata makes the COPY-FIRST decision fast and correct."""

    def test_groupedviolin_is_template_and_production_ready(self):
        lib = ProductionAssetLibrary()
        assets = lib.query("GroupedViolin")
        self.assertEqual(len(assets), 1)
        asset = assets[0]
        self.assertEqual(asset.asset_kind, "template")
        self.assertTrue(asset.production_ready)
        self.assertEqual(asset.runtime, "python")

    def test_stackedbarscatter_is_example_not_ready(self):
        lib = ProductionAssetLibrary()
        assets = lib.list(figure_type="StackedBarScatter")
        self.assertEqual(len(assets), 1)
        asset = assets[0]
        self.assertEqual(asset.asset_kind, "example")
        self.assertFalse(asset.production_ready)

    def test_pca_is_example_not_ready(self):
        lib = ProductionAssetLibrary()
        assets = lib.list(figure_type="PCA")
        self.assertEqual(len(assets), 1)
        asset = assets[0]
        self.assertEqual(asset.asset_kind, "example")
        self.assertEqual(asset.runtime, "r")

    def test_metadata_query_prefers_ready_templates(self):
        lib = ProductionAssetLibrary()
        assets = lib.query("heatmap")
        self.assertTrue(all(a.production_ready for a in assets))


class TestVisualReferenceRetrieval(unittest.TestCase):
    """Verify Phase 5 references are discoverable and tagged correctly."""

    def test_raincloud_reference_for_groupedviolin(self):
        refs = ReferenceLibrary().query(
            figure_type="GroupedViolin",
            tags=["raincloud"],
            review_status="reviewed",
        )
        # ``query`` ranks tag matches; it intentionally does not treat tags as
        # a strict filter because a figure can contribute useful grammar under
        # a different subtype.  Keep the matching raincloud reference first
        # while allowing other reviewed GroupedViolin references to remain
        # discoverable.
        self.assertGreaterEqual(len(refs), 1)
        self.assertIn("raincloud", [tag.lower() for tag in refs[0].metadata.get("tags", [])])
        self.assertEqual(refs[0].metadata.get("subtype"), "raincloud")
        self.assertEqual(refs[0].metadata.get("palette_policy"), "adaptable")

    def test_superplot_reference_for_stackedbarscatter(self):
        refs = ReferenceLibrary().query(
            figure_type="StackedBarScatter",
            tags=["superplot"],
            review_status="reviewed",
        )
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].metadata.get("subtype"), "superplot")
        self.assertEqual(refs[0].metadata.get("palette_policy"), "preserve")

    def test_complexheatmap_reference_for_heatmap(self):
        refs = ReferenceLibrary().query(
            figure_type="heatmap",
            tags=["complexheatmap"],
            review_status="reviewed",
        )
        # Query uses tags for ranking, not strict filtering; ensure the
        # complexheatmap reference is present and ranked first.
        subtypes = [r.metadata.get("subtype") for r in refs]
        self.assertIn("complexheatmap", subtypes)
        self.assertEqual(refs[0].metadata.get("subtype"), "complexheatmap")
        self.assertEqual(refs[0].metadata.get("palette_policy"), "preserve")


class TestVisualStyleResolution(unittest.TestCase):
    """Verify palette priority and reference policy behavior."""

    def test_groupedviolin_raincloud_adaptable_yields_colors(self):
        refs = ReferenceLibrary().query(
            figure_type="GroupedViolin",
            tags=["raincloud"],
            limit=1,
        )
        self.assertTrue(len(refs) > 0)
        style = resolve_visual_style(
            figure_type="GroupedViolin",
            reference_id=refs[0].id,
            n=4,
        )
        self.assertEqual(len(style["colors"]), 4)
        self.assertEqual(style["palette_policy"], "adaptable")
        self.assertEqual(style["source"], "reference")

    def test_user_colors_override_reference(self):
        refs = ReferenceLibrary().query(figure_type="GroupedViolin", tags=["raincloud"], limit=1)
        style = resolve_visual_style(
            figure_type="GroupedViolin",
            reference_id=refs[0].id,
            user_colors=["#000000", "#FFFFFF"],
            n=4,
        )
        self.assertEqual(style["colors"], ["#000000", "#FFFFFF"])
        self.assertEqual(style["source"], "user_colors")

    def test_wrong_reference_type_is_rejected_by_style_resolution(self):
        wrong_refs = ReferenceLibrary().query(
            figure_type="StackedBarScatter", tags=["superplot"], limit=1
        )
        with self.assertRaises(ValueError):
            resolve_visual_style(
                figure_type="GroupedViolin", reference_id=wrong_refs[0].id, n=4
            )

    def test_unknown_reference_id_is_not_silently_replaced_by_default_palette(self):
        with self.assertRaises(ValueError):
            resolve_visual_style(
                figure_type="GroupedViolin", reference_id="missing-reference", n=4
            )

    def test_invalid_reference_is_rejected_even_when_user_colors_override(self):
        with self.assertRaises(ValueError):
            resolve_visual_style(
                figure_type="GroupedViolin",
                reference_id="missing-reference",
                user_colors=["#000000", "#FFFFFF"],
                n=2,
            )


class TestProductionSemanticsPreserved(unittest.TestCase):
    """Verify reference cannot override figure type or data semantics."""

    def test_wrong_reference_does_not_change_figure_type(self):
        # User asks for GroupedViolin. Agent must not use StackedBarScatter
        # reference to change the figure type.
        production_asset = ProductionAssetLibrary().query("GroupedViolin")[0]
        wrong_refs = ReferenceLibrary().query(
            figure_type="StackedBarScatter",
            tags=["superplot"],
            limit=1,
        )
        self.assertEqual(len(wrong_refs), 1)

        # The agent should ignore cross-type references. Simulate by querying
        # only same-type references.
        same_type_refs = ReferenceLibrary().query(
            figure_type=production_asset.figure_type,
            tags=["raincloud"],
            limit=1,
        )
        self.assertEqual(len(same_type_refs), 1)
        self.assertNotEqual(wrong_refs[0].figure_type, production_asset.figure_type)

    def test_production_asset_determines_data_shape(self):
        asset = ProductionAssetLibrary().query("GroupedViolin")[0]
        self.assertEqual(asset.metadata.get("data_shape"), "wide")
        # A raincloud reference should not change this requirement.
        refs = ReferenceLibrary().query(figure_type="GroupedViolin", tags=["raincloud"])
        self.assertEqual(refs[0].metadata.get("data_shape"), None)


class TestRenderWithReferenceVisualLanguage(unittest.TestCase):
    """Actually render figures combining production asset + reference."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_wide_data(self, groups: list) -> pd.DataFrame:
        rng = np.random.default_rng(42)
        return pd.DataFrame({g: rng.normal(loc=5 + i * 0.5, scale=1.0, size=50) for i, g in enumerate(groups)})

    def test_render_raincloud_groupedviolin(self):
        """GroupedViolin production logic + raincloud reference visual language."""
        production_asset = ProductionAssetLibrary().query("GroupedViolin")[0]
        refs = ReferenceLibrary().query(
            figure_type="GroupedViolin",
            tags=["raincloud"],
            limit=1,
        )
        ref = refs[0]
        style = resolve_visual_style(
            figure_type="GroupedViolin",
            reference_id=ref.id,
            n=4,
        )

        groups = ["A", "B", "C", "D"]
        df = self._make_wide_data(groups)
        positions = np.arange(1, len(groups) + 1)

        fig, ax = plt.subplots(figsize=(6, 4))
        # Violins (core GroupedViolin semantics from production asset).
        parts = ax.violinplot(
            [df[g].dropna().values for g in groups],
            positions=positions,
            showmeans=False,
            showmedians=False,
            showextrema=False,
            widths=0.7,
        )
        for body, color in zip(parts["bodies"], style["colors"]):
            body.set_facecolor(color)
            body.set_alpha(0.5)

        # Jitter (raincloud visual language from reference).
        rng = np.random.default_rng(42)
        for i, (g, color) in enumerate(zip(groups, style["colors"])):
            y = df[g].dropna().values
            x = rng.normal(positions[i] + 0.25, 0.03, size=len(y))
            ax.scatter(x, y, s=10, c=color, alpha=0.6)

        ax.set_xticks(positions)
        ax.set_xticklabels(groups)
        out_path = self.out_dir / "raincloud_groupedviolin.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)

        self.assertTrue(out_path.exists())
        self.assertGreater(out_path.stat().st_size, 0)

        # Visual Source Report fields.
        report = {
            "production_asset": f"{production_asset.figure_type}/{production_asset.metadata.get('preview', 'script')}",
            "visual_reference": ref.id,
            "palette": style["palette"],
            "palette_policy": style["palette_policy"],
            "output_png": str(out_path),
        }
        self.assertIsNotNone(report["visual_reference"])
        self.assertEqual(report["palette_policy"], "adaptable")

    def test_render_superplot_stackedbarscatter(self):
        """StackedBarScatter production logic + SuperPlots reference visual language."""
        production_asset = ProductionAssetLibrary().list(figure_type="StackedBarScatter")[0]
        refs = ReferenceLibrary().query(
            figure_type="StackedBarScatter",
            tags=["superplot"],
            limit=1,
        )
        ref = refs[0]
        style = resolve_visual_style(
            figure_type="StackedBarScatter",
            reference_id=ref.id,
            n=3,
        )

        rng = np.random.default_rng(2025)
        groups = ["WT", "KO-1", "KO-2"]
        fig, ax = plt.subplots(figsize=(5, 4))

        for i, (g, color) in enumerate(zip(groups, style["colors"])):
            for r in range(4):
                y = rng.normal(loc=5 + i * 0.7, scale=0.6, size=10)
                x = rng.normal(i + 1 + (r - 1.5) * 0.12, 0.02, size=10)
                ax.scatter(x, y, s=20, c=color, alpha=0.7)
            mean = rng.normal(5 + i * 0.7, 0.2)
            ax.errorbar(i + 1, mean, yerr=0.15, fmt="o", markersize=8,
                        markerfacecolor="white", markeredgecolor="black", ecolor="black")

        ax.set_xticks(range(1, len(groups) + 1))
        ax.set_xticklabels(groups)
        out_path = self.out_dir / "superplot_stackedbarscatter.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)

        self.assertTrue(out_path.exists())
        self.assertEqual(style["palette_policy"], "preserve")
        self.assertEqual(production_asset.asset_kind, "example")

    def test_render_complexheatmap_heatmap(self):
        """heatmap production logic + ComplexHeatmap reference visual language."""
        production_asset = ProductionAssetLibrary().query("heatmap")[0]
        refs = ReferenceLibrary().query(
            figure_type="heatmap",
            tags=["complexheatmap"],
            limit=1,
        )
        ref = refs[0]
        style = resolve_visual_style(figure_type="heatmap", reference_id=ref.id, n=3)

        rng = np.random.default_rng(11)
        data = rng.standard_normal((16, 8))
        fig, ax = plt.subplots(figsize=(5, 5))
        im = ax.imshow(data, aspect="auto", cmap="RdBu_r", vmin=-2.5, vmax=2.5)
        fig.colorbar(im, ax=ax)
        out_path = self.out_dir / "complexheatmap_heatmap.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)

        self.assertTrue(out_path.exists())
        self.assertEqual(production_asset.asset_kind, "reusable")


if __name__ == "__main__":
    unittest.main()
