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

SPEC = {'source_fingerprint': 'dc61a5257eae4748348c72c51f2e70e59979c6892f52dadf7bb4ba6f8b98b00b', 'width': 1500, 'height': 1207, 'visual_family': 'forest_interval', 'observable_visual_grammar': {'panel_grid': [4, 4], 'panel_count': 16, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'forest_interval'}, 'reconstruction_blueprint': {'blueprint_id': 'atlas_forest_interval', 'mosaic': ['ABCD', 'EFGH', 'IJKL', 'MNOP'], 'panel_recipes': [{'id': 'A', 'kind': 'forest:atlas'}, {'id': 'B', 'kind': 'forest:atlas'}, {'id': 'C', 'kind': 'forest:atlas'}, {'id': 'D', 'kind': 'forest:atlas'}, {'id': 'E', 'kind': 'forest:atlas'}, {'id': 'F', 'kind': 'forest:atlas'}, {'id': 'G', 'kind': 'forest:atlas'}, {'id': 'H', 'kind': 'forest:atlas'}, {'id': 'I', 'kind': 'forest:atlas'}, {'id': 'J', 'kind': 'forest:atlas'}, {'id': 'K', 'kind': 'forest:atlas'}, {'id': 'L', 'kind': 'forest:atlas'}, {'id': 'M', 'kind': 'forest:atlas'}, {'id': 'N', 'kind': 'forest:atlas'}, {'id': 'O', 'kind': 'forest:atlas'}, {'id': 'P', 'kind': 'forest:atlas'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': '16 interval and effect-size variants arranged as an atlas'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
