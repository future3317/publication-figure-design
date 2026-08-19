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

SPEC = {'source_fingerprint': '9a8189149180a68679738bc4be152ee40b17d71261d71b3759d315a7169da0d9', 'width': 1500, 'height': 1207, 'visual_family': 'line_grid', 'observable_visual_grammar': {'panel_grid': [4, 4], 'panel_count': 16, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'line_grid'}, 'reconstruction_blueprint': {'blueprint_id': 'atlas_line_trends', 'mosaic': ['ABCD', 'EFGH', 'IJKL', 'MNOP'], 'panel_recipes': [{'id': 'A', 'kind': 'line:atlas'}, {'id': 'B', 'kind': 'line:atlas'}, {'id': 'C', 'kind': 'line:atlas'}, {'id': 'D', 'kind': 'line:atlas'}, {'id': 'E', 'kind': 'line:atlas'}, {'id': 'F', 'kind': 'line:atlas'}, {'id': 'G', 'kind': 'line:atlas'}, {'id': 'H', 'kind': 'line:atlas'}, {'id': 'I', 'kind': 'line:atlas'}, {'id': 'J', 'kind': 'line:atlas'}, {'id': 'K', 'kind': 'line:atlas'}, {'id': 'L', 'kind': 'line:atlas'}, {'id': 'M', 'kind': 'line:atlas'}, {'id': 'N', 'kind': 'line:atlas'}, {'id': 'O', 'kind': 'line:atlas'}, {'id': 'P', 'kind': 'line:atlas'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': '16 trend and uncertainty variants arranged as an atlas'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
