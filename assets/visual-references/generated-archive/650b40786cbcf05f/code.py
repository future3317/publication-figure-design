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

SPEC = {'source_fingerprint': 'e7fa7d98cd4f5263f5550d7ac8824e60071c20b2927aef52ac6d18d62fd29ffa', 'width': 1500, 'height': 1216, 'visual_family': 'radar_grid', 'observable_visual_grammar': {'panel_grid': [4, 4], 'panel_count': 16, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'radar_grid'}, 'reconstruction_blueprint': {'blueprint_id': 'atlas_radar_polar', 'mosaic': ['ABCD', 'EFGH', 'IJKL', 'MNOP'], 'panel_recipes': [{'id': 'A', 'kind': 'radar:atlas'}, {'id': 'B', 'kind': 'radar:atlas'}, {'id': 'C', 'kind': 'radar:atlas'}, {'id': 'D', 'kind': 'radar:atlas'}, {'id': 'E', 'kind': 'radar:atlas'}, {'id': 'F', 'kind': 'radar:atlas'}, {'id': 'G', 'kind': 'radar:atlas'}, {'id': 'H', 'kind': 'radar:atlas'}, {'id': 'I', 'kind': 'radar:atlas'}, {'id': 'J', 'kind': 'radar:atlas'}, {'id': 'K', 'kind': 'radar:atlas'}, {'id': 'L', 'kind': 'radar:atlas'}, {'id': 'M', 'kind': 'radar:atlas'}, {'id': 'N', 'kind': 'radar:atlas'}, {'id': 'O', 'kind': 'radar:atlas'}, {'id': 'P', 'kind': 'radar:atlas'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': '16 polar-chart variants arranged as an atlas'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
