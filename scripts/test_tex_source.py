from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_tex_source import check_tex_source


class TexSourceChecks(unittest.TestCase):
    def test_valid_pgfplots_source_requires_compatibility_and_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "figure.tex"
            source.write_text(
                r"""\documentclass{standalone}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\begin{document}
\begin{tikzpicture}\begin{axis}[width=\linewidth]\addplot coordinates {(0,0) (1,1)};\end{axis}\end{tikzpicture}
\end{document}
""",
                encoding="utf-8",
            )
            report = check_tex_source(source)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["errors"], [])

    def test_shell_escape_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "unsafe.tex"
            source.write_text(r"\documentclass{standalone}\write18{curl example.com}\begin{document}\end{document}", encoding="utf-8")
            report = check_tex_source(source)
        self.assertFalse(report["ok"])
        self.assertTrue(any("shell escape" in item.lower() for item in report["errors"]))

    def test_pgftikz_without_compatibility_is_actionable_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "compat.tex"
            source.write_text(r"\documentclass{standalone}\usepackage{pgfplots}\begin{document}\begin{tikzpicture}\begin{axis}\end{axis}\end{tikzpicture}\end{document}", encoding="utf-8")
            report = check_tex_source(source)
        self.assertTrue(report["ok"], report)
        self.assertTrue(any("compat" in item.lower() for item in report["warnings"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
