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

SPEC = {'source_fingerprint': 'cd1fec84f615a43dbe91cc94bfbb94fe07e086fdd5d8191fbff2ec990e38d4f5', 'width': 2700, 'height': 1500, 'visual_family': 'comparison_composite', 'observable_visual_grammar': {'panel_grid': [1, 2], 'panel_count': 2, 'aspect_class': 'wide', 'density': 'focused', 'visual_family': 'comparison_composite'}, 'reconstruction_blueprint': {'blueprint_id': 'rnagenscape_speed', 'mosaic': ['AB'], 'panel_recipes': [{'id': 'A', 'kind': 'bar:comparison'}, {'id': 'B', 'kind': 'forest:effects'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'speed comparison with effect-size intervals'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
