# -*- coding: utf-8 -*-
"""Real E2E smoke test: reference retrieval -> style adaptation -> render -> report.

This script creates two temporary visual references (preserve + adaptable),
queries them for a GroupedViolin figure, generates a simple grouped violin plot
using the selected reference palette, and writes a Visual Source Report.

Run:
    python scripts/e2e_smoke_test.py

The temporary visual references are deleted before the script exits.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Ensure the skill root is on the path for imports.
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from reference_library import ReferenceLibrary


def _make_png(path: Path, color: bytes = b"\x89PNG\r\n\x1a\n") -> Path:
    """Create a minimal PNG-like file."""
    path.write_bytes(color)
    return path


def _render_figure(colors: list[str], output_path: Path) -> None:
    """Generate a simple grouped violin plot with the given colors."""
    code = f"""
import matplotlib.pyplot as plt
import numpy as np

# Dummy data: three groups, two conditions
data = {{
    "A": np.random.default_rng(42).normal(0, 1, 100),
    "B": np.random.default_rng(43).normal(1.2, 1.1, 100),
    "C": np.random.default_rng(44).normal(2.0, 0.9, 100),
}}

fig, ax = plt.subplots(figsize=(4, 3))
parts = ax.violinplot([data[k] for k in data], showmeans=False, showmedians=True)
for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor({colors!r}[i])
    pc.set_edgecolor("black")
    pc.set_alpha(0.8)

ax.set_xticks(range(1, len(data) + 1))
ax.set_xticklabels(list(data.keys()))
ax.set_title("Smoke test grouped violin")
fig.savefig({str(output_path)!r}, dpi=150)
plt.close(fig)
"""
    tmp_py = output_path.parent / "_smoke_render.py"
    tmp_py.write_text(code, encoding="utf-8")
    try:
        subprocess.run([sys.executable, str(tmp_py)], check=True)
    finally:
        tmp_py.unlink(missing_ok=True)


def run_smoke() -> dict:
    """Run the full smoke test and return the Visual Source Report."""
    # Use a temporary skill root so we can clean up everything afterwards.
    tmp_root = Path(tempfile.mkdtemp(prefix="afs_phase3_smoke_"))
    (tmp_root / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    lib = ReferenceLibrary(root=tmp_root)

    try:
        # 1. Ingest two temporary visual references for GroupedViolin.
        preserve_img = _make_png(tmp_root / "preserve_ref.png", b"\x89PNG\r\n\x1a\nPRESERVE")
        adaptable_img = _make_png(tmp_root / "adaptable_ref.png", b"\x89PNG\r\n\x1a\nADAPTABLE")

        ref_preserve = lib.ingest(
            preserve_img,
            "GroupedViolin",
            metadata_override={
                "tags": ["pastel", "minimal"],
                "palette": "summer_beach",
                "palette_policy": "preserve",
                "journal_style": "Nature",
                "n_groups": 3,
            },
        )
        review = {
            "final_size_inspected": True, "hierarchy": "pass", "panel_balance": "pass",
            "whitespace": "pass", "legend_footprint": "pass", "text_legibility": "pass",
            "reviewer": "e2e rendered review",
        }
        ref_preserve = lib.review(ref_preserve.id, 4, review)

        ref_adaptable = lib.ingest(
            adaptable_img,
            "GroupedViolin",
            metadata_override={
                "tags": ["bold", "high-contrast"],
                "palette": "sweet_macaron",
                "palette_policy": "adaptable",
                "journal_style": "Cell",
                "n_groups": 3,
            },
        )
        ref_adaptable = lib.review(ref_adaptable.id, 4, review)

        # 2. Query for GroupedViolin references matching "pastel" + "Nature".
        refs = lib.query(
            figure_type="GroupedViolin",
            tags=["pastel"],
            journal_style="Nature",
            n_groups=3,
            min_aesthetic_rating=3,
            limit=3,
        )
        assert len(refs) >= 1, "Expected at least one matching reference"
        selected = refs[0]
        assert selected.metadata["palette_policy"] == "preserve"

        # 3. Resolve palette for the selected reference.
        from palette_manager import get_palette
        colors = get_palette(selected.metadata["palette"], n=3)

        # 4. Render a grouped violin figure with the selected reference palette.
        output_png = tmp_root / "smoke_output.png"
        _render_figure(colors, output_png)
        assert output_png.exists(), "Smoke render did not produce PNG"

        # 5. Build Visual Source Report.
        report = {
            "production_asset": "GroupedViolin/plot_GroupedViolin.py",
            "visual_reference": selected.id,
            "palette": selected.metadata["palette"],
            "palette_policy": selected.metadata["palette_policy"],
            "output_png": str(output_png),
            "colors": colors,
        }

        # 6. Verify adaptable path: query bold/Cell and ensure palette_policy=adaptable.
        adapt_refs = lib.query(
            figure_type="GroupedViolin",
            tags=["bold"],
            journal_style="Cell",
            limit=3,
        )
        assert len(adapt_refs) >= 1
        assert adapt_refs[0].metadata["palette_policy"] == "adaptable"

        return report

    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def main() -> int:
    report = run_smoke()
    print("E2E smoke test PASSED")
    print("Visual Source Report:")
    for key, value in report.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
