# -*- coding: utf-8 -*-
"""Unit tests for palette_manager.py."""

import sys
import unittest
from pathlib import Path

# Ensure the script directory is importable when running standalone.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from palette_manager import (
    extend_palette,
    get_palette,
    get_palette_info,
    list_palettes,
    resolve_colors,
    resolve_palette,
    set_default_palette,
    validate_palettes,
)
from palettes import PALETTES, ZH_TO_ID


class TestPaletteValidation(unittest.TestCase):
    def test_all_palettes_are_valid(self):
        ok, errors = validate_palettes()
        self.assertTrue(ok, "\n".join(errors))

    def test_each_palette_has_eight_valid_hex_colors(self):
        hex_pattern = "#[0-9A-Fa-f]{6}"
        for pid, info in PALETTES.items():
            colors = info["colors"]
            self.assertEqual(len(colors), 8, f"{pid}: expected 8 colors")
            for c in colors:
                self.assertRegex(c, hex_pattern, f"{pid}: invalid hex {c!r}")


class TestPaletteAccess(unittest.TestCase):
    def test_list_palettes_returns_metadata(self):
        palettes = list_palettes()
        self.assertEqual(len(palettes), len(PALETTES))
        for entry in palettes:
            self.assertIn("id", entry)
            self.assertIn("name_zh", entry)
            self.assertIn("tags", entry)

    def test_get_palette_by_id(self):
        colors = get_palette("summer_beach")
        self.assertEqual(colors, PALETTES["summer_beach"]["colors"])

    def test_get_palette_by_chinese_name(self):
        for zh_name, pid in ZH_TO_ID.items():
            colors = get_palette(zh_name)
            self.assertEqual(colors, PALETTES[pid]["colors"])

    def test_get_palette_info(self):
        info = get_palette_info("pastel_girl")
        self.assertEqual(info["name_zh"], "粉彩少女")
        self.assertIn("tags", info)
        self.assertEqual(info["type"], "categorical")


class TestPaletteSubsetting(unittest.TestCase):
    def test_n_zero_returns_empty(self):
        self.assertEqual(get_palette("summer_beach", 0), [])

    def test_n_less_than_palette_length(self):
        colors = get_palette("summer_beach", 3)
        self.assertEqual(len(colors), 3)
        self.assertEqual(colors, PALETTES["summer_beach"]["colors"][:3])

    def test_n_equal_to_palette_length(self):
        colors = get_palette("summer_beach", 8)
        self.assertEqual(len(colors), 8)
        self.assertEqual(colors, PALETTES["summer_beach"]["colors"])

    def test_subset_is_deterministic(self):
        self.assertEqual(get_palette("soft_forest", 4), get_palette("soft_forest", 4))


class TestPaletteExtension(unittest.TestCase):
    def test_extension_preserves_base_colors(self):
        base = PALETTES["summer_beach"]["colors"]
        extended = extend_palette("summer_beach", 12)
        self.assertEqual(len(extended), 12)
        # Base colors must appear in their original order.
        base_indices = [extended.index(c) for c in base]
        self.assertEqual(base_indices, sorted(base_indices))

    def test_extension_is_deterministic(self):
        self.assertEqual(extend_palette("fresh_holiday", 11), extend_palette("fresh_holiday", 11))

    def test_extension_no_cycling(self):
        base = PALETTES["sweet_macaron"]["colors"]
        extended = extend_palette("sweet_macaron", 20)
        # No simple cycle of the first 8 colors.
        self.assertEqual(len(set(extended)), len(extended))
        self.assertTrue(all(c in extended for c in base))

    def test_get_palette_auto_extends(self):
        colors = get_palette("watercolor_bloom", 15)
        self.assertEqual(len(colors), 15)
        self.assertEqual(colors[:8], PALETTES["watercolor_bloom"]["colors"])


class TestResolveAndDefault(unittest.TestCase):
    def setUp(self):
        self._original_default = "pastel_girl"
        set_default_palette(self._original_default)

    def tearDown(self):
        set_default_palette(self._original_default)

    def test_resolve_palette_uses_default_when_none(self):
        set_default_palette("blue_green_land")
        colors = resolve_palette(None)
        self.assertEqual(colors, PALETTES["blue_green_land"]["colors"])

    def test_resolve_palette_with_explicit_name(self):
        colors = resolve_palette("summer_beach")
        self.assertEqual(colors, PALETTES["summer_beach"]["colors"])

    def test_set_default_palette_accepts_chinese_name(self):
        set_default_palette("柔绿森林")
        self.assertEqual(resolve_palette(None), PALETTES["soft_forest"]["colors"])


class TestResolveColorsPriority(unittest.TestCase):
    def test_explicit_colors_win_over_palette(self):
        explicit = ["#FF0000", "#00FF00"]
        colors = resolve_colors(colors=explicit, palette="summer_beach")
        self.assertEqual(colors, explicit)

    def test_explicit_palette_used_when_no_explicit_colors(self):
        colors = resolve_colors(colors=None, palette="fresh_holiday", n=4)
        self.assertEqual(colors, PALETTES["fresh_holiday"]["colors"][:4])

    def test_default_palette_used_when_nothing_specified(self):
        set_default_palette("pastel_girl")
        colors = resolve_colors(colors=None, palette=None, n=3)
        self.assertEqual(colors, PALETTES["pastel_girl"]["colors"][:3])


class TestErrorHandling(unittest.TestCase):
    def test_unknown_palette_raises_clear_error(self):
        with self.assertRaises(ValueError) as ctx:
            get_palette("not_a_palette")
        msg = str(ctx.exception)
        self.assertIn("Unknown palette name", msg)
        self.assertIn("summer_beach", msg)

    def test_negative_n_raises(self):
        with self.assertRaises(ValueError):
            get_palette("summer_beach", -1)

    def test_invalid_n_type_raises(self):
        with self.assertRaises(TypeError):
            get_palette("summer_beach", "five")


if __name__ == "__main__":
    unittest.main()
