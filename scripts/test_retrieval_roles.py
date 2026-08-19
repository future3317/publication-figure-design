import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from publication_figure_design.references.retrieval import MultiRoleReferenceRetriever


def test_retrieval_returns_separate_roles_and_cross_type_style():
    refs = [
        {"id": "bar", "figure_type": "grouped_bar", "review_status": "reviewed", "tags": ["minimal"], "layout": "wide", "visual_grammar": {"palette_roles": {"ours": "#123456"}}, "aesthetic_rating": 5},
        {"id": "scatter", "figure_type": "scatter_bubble", "review_status": "reviewed", "tags": ["minimal", "nature"], "layout": "wide", "visual_grammar": {"palette_roles": {"ours": "#123456"}}, "aesthetic_rating": 5},
    ]
    result = MultiRoleReferenceRetriever(references=refs).retrieve(figure_type="grouped_bar", tags=["minimal"], layout="wide", limit=1)
    assert set(result) == set(MultiRoleReferenceRetriever.ROLES)
    assert result["style_reference"][0]["id"] in {"bar", "scatter"}
    assert "reference_alignment_score" in result["style_reference"][0]
    assert "aesthetic_quality_score" in result["style_reference"][0]
    assert result["style_reference"][0]["aesthetic_quality_score"] == 1.0
