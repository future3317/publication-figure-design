#!/usr/bin/env python3
"""Reproduce this independently generated visual-grammar example."""

import sys
import importlib.util
from pathlib import Path
SKILL_ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = SKILL_ROOT / 'scripts' / 'source_reconstruction_library.py'
sys.path.insert(0, str(MODULE_PATH.parent))
module_spec = importlib.util.spec_from_file_location('source_reconstruction_library', MODULE_PATH)
module = importlib.util.module_from_spec(module_spec)
sys.modules[module_spec.name] = module
module_spec.loader.exec_module(module)
render_from_spec = module.render_from_spec

SPEC = {'source_fingerprint': '245ad31f97b2054628987444e44d6a007f352f65ae6254189f5ed8ba9b0301c6', 'width': 1600, 'height': 1424, 'visual_family': 'validation_perturbation', 'observable_visual_grammar': {'panel_grid': [3, 4], 'panel_count': 12, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'validation_perturbation'}, 'reconstruction_blueprint': {'blueprint_id': 'gallery_validation_perturbation', 'mosaic': ['AABB', 'CCDE'], 'panel_recipes': [{'id': 'A', 'kind': 'schematic:perturbation'}, {'id': 'B', 'kind': 'scatter:validation'}, {'id': 'C', 'kind': 'bar:ablation'}, {'id': 'D', 'kind': 'heatmap:response'}, {'id': 'E', 'kind': 'forest:effects'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'perturbation workflow and validation evidence across scatter, ablation, matrix, interval panels'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
