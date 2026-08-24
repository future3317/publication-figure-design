from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from check_references import check_reference_evidence_content_types
except ImportError:  # pragma: no cover
    from scripts.check_references import check_reference_evidence_content_types


class ReferenceEvidenceContentTests(unittest.TestCase):
    def test_repository_evidence_files_match_their_extensions(self) -> None:
        report = check_reference_evidence_content_types(Path(__file__).resolve().parents[1])
        self.assertEqual(report, [])

    def test_png_with_json_content_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = root / "assets" / "visual-references" / "review-evidence"
            evidence.mkdir(parents=True)
            (evidence / "bad.png").write_text('{"ssim": 0.9}\n', encoding="utf-8")
            self.assertEqual(check_reference_evidence_content_types(root), [
                "bad.png: .png does not contain a matching image signature"
            ])


if __name__ == "__main__":
    unittest.main()
