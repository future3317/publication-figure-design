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

SPEC = {'source_fingerprint': '4cf8539d0521b7268f0227b56cecddf2f70c1bb4bbcf9b5e3be886e95a54927a', 'width': 6000, 'height': 2700, 'visual_family': 'comparison_composite', 'observable_visual_grammar': {'panel_grid': [1, 2], 'panel_count': 2, 'aspect_class': 'wide', 'density': 'focused', 'visual_family': 'comparison_composite'}, 'reconstruction_blueprint': {'blueprint_id': 'rnagenscape_optimization', 'mosaic': ['AABB', 'CCDD'], 'panel_recipes': [{'id': 'A', 'kind': 'heatmap:optimization'}, {'id': 'B', 'kind': 'line:optimization'}, {'id': 'C', 'kind': 'bar:comparison'}, {'id': 'D', 'kind': 'scatter:embedding'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'optimization landscape hero with trajectory, method comparison, and embedding'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
