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

SPEC = {'source_fingerprint': '350c25e427d945dee5fd98316eb6ebe307304b9d187d954a88c05852d664a60b', 'width': 1500, 'height': 1183, 'visual_family': 'area_stacked', 'observable_visual_grammar': {'panel_grid': [4, 4], 'panel_count': 16, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'area_stacked'}, 'reconstruction_blueprint': {'blueprint_id': 'atlas_area_stacked', 'mosaic': ['ABCD', 'EFGH', 'IJKL', 'MNOP'], 'panel_recipes': [{'id': 'A', 'kind': 'area:atlas'}, {'id': 'B', 'kind': 'area:atlas'}, {'id': 'C', 'kind': 'area:atlas'}, {'id': 'D', 'kind': 'area:atlas'}, {'id': 'E', 'kind': 'area:atlas'}, {'id': 'F', 'kind': 'area:atlas'}, {'id': 'G', 'kind': 'area:atlas'}, {'id': 'H', 'kind': 'area:atlas'}, {'id': 'I', 'kind': 'area:atlas'}, {'id': 'J', 'kind': 'area:atlas'}, {'id': 'K', 'kind': 'area:atlas'}, {'id': 'L', 'kind': 'area:atlas'}, {'id': 'M', 'kind': 'area:atlas'}, {'id': 'N', 'kind': 'area:atlas'}, {'id': 'O', 'kind': 'area:atlas'}, {'id': 'P', 'kind': 'area:atlas'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': '16 stacked-area and composition variants arranged as an atlas'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
