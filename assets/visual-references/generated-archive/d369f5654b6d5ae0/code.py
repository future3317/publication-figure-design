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

SPEC = {'source_fingerprint': '91b214f745a99f1f2b472ddae7661dfa2d9241791768767180219315b89047ec', 'width': 10800, 'height': 1800, 'visual_family': 'comparison_composite', 'observable_visual_grammar': {'panel_grid': [1, 3], 'panel_count': 3, 'aspect_class': 'wide', 'density': 'medium', 'visual_family': 'comparison_composite'}, 'reconstruction_blueprint': {'blueprint_id': 'cflows_trajectory', 'mosaic': ['ABC'], 'panel_recipes': [{'id': 'A', 'kind': 'scatter:trajectory'}, {'id': 'B', 'kind': 'line:dynamics'}, {'id': 'C', 'kind': 'forest:effects'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'trajectory panel followed by dynamics and effect comparison'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
