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

SPEC = {'source_fingerprint': 'a6f2e75e7d8361754445d86ce04386b5764a46bf2cbc94e8df0c75ecf1bab142', 'width': 2700, 'height': 2400, 'visual_family': 'line_grid', 'observable_visual_grammar': {'panel_grid': [1, 1], 'panel_count': 1, 'aspect_class': 'balanced', 'density': 'focused', 'visual_family': 'line_grid'}, 'reconstruction_blueprint': {'blueprint_id': 'vigil_posttraining', 'mosaic': ['ABC'], 'panel_recipes': [{'id': 'A', 'kind': 'line:posttraining'}, {'id': 'B', 'kind': 'line:posttraining'}, {'id': 'C', 'kind': 'line:posttraining'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'three post-training comparison curves'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
