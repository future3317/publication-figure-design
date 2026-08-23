"""Layered publication-figure QA."""

from .anti_copy import anti_copy_check
from .color import check_palette
from .export import check_export
from .geometry import run_structural_qa
from .perceptual import run_perceptual_qa
from .scientific import run_scientific_qa
from .technical import run_hard_qa
from .typography import check_typography

__all__ = ["anti_copy_check", "check_export", "check_palette", "check_typography", "run_hard_qa", "run_perceptual_qa", "run_scientific_qa", "run_structural_qa"]
