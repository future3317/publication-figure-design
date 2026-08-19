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

SPEC = {'source_fingerprint': '66fe0f27f44697547b6cb219ff90696f54a6fef48984c9578ace258e0ebce4d4', 'width': 4200, 'height': 2400, 'visual_family': 'line_grid', 'observable_visual_grammar': {'panel_grid': [1, 2], 'panel_count': 2, 'aspect_class': 'wide', 'density': 'focused', 'visual_family': 'line_grid'}, 'reconstruction_blueprint': {'blueprint_id': 'ophthal_monthly_trend', 'mosaic': ['AB', 'CD'], 'panel_recipes': [{'id': 'A', 'kind': 'line:monthly'}, {'id': 'B', 'kind': 'line:monthly'}, {'id': 'C', 'kind': 'area:composition'}, {'id': 'D', 'kind': 'bar:summary'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'monthly trends, composition over time, and summary comparison'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
