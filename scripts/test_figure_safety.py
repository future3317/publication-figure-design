from __future__ import annotations

import os
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from audit_pdf_text import audit_pdf
from backend_preference import clear_backend, config_path, get_backend, set_backend
from figure_safety import interp_monotone, label_y_above


def fake_pdf(stream: bytes, compressed: bool = False) -> bytes:
    payload = zlib.compress(stream) if compressed else stream
    filter_entry = b" /Filter /FlateDecode" if compressed else b""
    return (
        b"%PDF-1.4\n1 0 obj\n<< /Length "
        + str(len(payload)).encode("ascii")
        + filter_entry
        + b" >>\nstream\n"
        + payload
        + b"\nendstream\nendobj\n%%EOF\n"
    )


class PdfAuditTests(unittest.TestCase):
    def test_plain_pdf_passes(self):
        report = audit_pdf(fake_pdf(b"BT /F1 7 Tf (Label) Tj ET"))
        self.assertTrue(report["auditable"])
        self.assertEqual(report["minimum_found_pt"], 7.0)
        self.assertEqual(report["below_minimum_count"], 0)

    def test_compressed_pdf_catches_small_script_glyph(self):
        report = audit_pdf(fake_pdf(b"BT /F1 7 Tf (R) Tj /F2 4.9 Tf (2) Tj ET", True))
        self.assertEqual(report["minimum_found_pt"], 4.9)
        self.assertEqual(report["below_minimum_count"], 1)

    def test_pdf_without_tf_is_not_auditable(self):
        self.assertFalse(audit_pdf(fake_pdf(b"0 0 m 10 10 l S"))["auditable"])


class NumericalSafetyTests(unittest.TestCase):
    def test_decreasing_grid_is_reversed_with_values(self):
        self.assertAlmostEqual(float(interp_monotone(7, [10, 8, 6], [5, 10, 15])), 12.5)

    def test_direction_change_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "strictly monotone"):
            interp_monotone(7, [10, 6, 8], [5, 10, 15])

    def test_label_clears_uncertainty(self):
        self.assertGreater(label_y_above([80, 90], [2, 6]), 96)


class BackendPreferenceTests(unittest.TestCase):
    def test_round_trip_and_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preferences.json"
            self.assertIsNone(get_backend(path))
            self.assertEqual(set_backend(path, "R"), "r")
            self.assertEqual(get_backend(path), "r")
            clear_backend(path)
            self.assertIsNone(get_backend(path))

    def test_environment_override(self):
        with patch.dict(os.environ, {"ACADEMIC_FIGURE_CONFIG": "./custom-pref.json"}):
            self.assertEqual(config_path(), Path("custom-pref.json"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
