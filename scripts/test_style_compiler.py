import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication_figure_design.style.compiler import StyleSpec, apply_style_spec_matplotlib, apply_style_spec_svg, build_image_generation_style_prompt


def test_style_spec_contains_machine_readable_contract():
    spec = StyleSpec.from_dict({"canvas": {"background": "#111111"}, "palette": {"roles": {"ours": "#E69F00"}}})
    assert spec.canvas["background"] == "#111111"
    assert spec.palette["roles"]["ours"] == "#E69F00"
    assert "strokes" in spec.to_dict() and "density" in spec.to_dict()


def test_renderers_consume_same_spec():
    spec = StyleSpec.from_dict({"typography": {"family": "Arial", "body_size": 10, "title_size": 14, "tick_size": 8, "annotation_size": 8}, "canvas": {"background": "#FAFAFA"}})
    rc = {"font.family": None, "font.size": None, "axes.titlesize": None, "axes.labelsize": None, "xtick.labelsize": None, "ytick.labelsize": None, "axes.linewidth": None, "grid.linewidth": None, "grid.color": None, "grid.alpha": None, "grid.linestyle": None, "xtick.direction": None, "ytick.direction": None, "xtick.major.size": None, "ytick.major.size": None, "xtick.major.width": None, "ytick.major.width": None, "axes.facecolor": None, "figure.facecolor": None, "legend.fontsize": None, "legend.frameon": None}
    apply_style_spec_matplotlib(spec, rc=rc)
    assert rc["font.family"] == "Arial"
    assert apply_style_spec_svg(spec)["font_family"] == "Arial"
    assert "Arial" in build_image_generation_style_prompt(spec)
