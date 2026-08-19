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

SPEC = {'source_fingerprint': '4a0e3040bbdbfe5ec48b66515f719f83ad7304fadb2e56432cd3e8f7ccbabd65', 'width': 1500, 'height': 1190, 'visual_family': 'grouped_bar', 'observable_visual_grammar': {'panel_grid': [4, 4], 'panel_count': 16, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'grouped_bar'}, 'reconstruction_blueprint': {'blueprint_id': 'atlas_bar_charts', 'mosaic': ['ABCD', 'EFGH', 'IJKL', 'MNOP'], 'panel_recipes': [{'id': 'A', 'kind': 'bar:atlas'}, {'id': 'B', 'kind': 'bar:atlas'}, {'id': 'C', 'kind': 'bar:atlas'}, {'id': 'D', 'kind': 'bar:atlas'}, {'id': 'E', 'kind': 'bar:atlas'}, {'id': 'F', 'kind': 'bar:atlas'}, {'id': 'G', 'kind': 'bar:atlas'}, {'id': 'H', 'kind': 'bar:atlas'}, {'id': 'I', 'kind': 'bar:atlas'}, {'id': 'J', 'kind': 'bar:atlas'}, {'id': 'K', 'kind': 'bar:atlas'}, {'id': 'L', 'kind': 'bar:atlas'}, {'id': 'M', 'kind': 'bar:atlas'}, {'id': 'N', 'kind': 'bar:atlas'}, {'id': 'O', 'kind': 'bar:atlas'}, {'id': 'P', 'kind': 'bar:atlas'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': '16 bar-chart variants arranged as an atlas'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
