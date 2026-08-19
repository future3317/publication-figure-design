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

SPEC = {'source_fingerprint': '1bbfbc38a3f246e4fd7c59b9ed1003ddbc7280ee160b7c38abf8d410b27fe6f8', 'width': 1500, 'height': 1183, 'visual_family': 'scatter_bubble', 'observable_visual_grammar': {'panel_grid': [4, 4], 'panel_count': 16, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'scatter_bubble'}, 'reconstruction_blueprint': {'blueprint_id': 'atlas_scatter_bubble', 'mosaic': ['ABCD', 'EFGH', 'IJKL', 'MNOP'], 'panel_recipes': [{'id': 'A', 'kind': 'scatter:atlas'}, {'id': 'B', 'kind': 'scatter:atlas'}, {'id': 'C', 'kind': 'scatter:atlas'}, {'id': 'D', 'kind': 'scatter:atlas'}, {'id': 'E', 'kind': 'scatter:atlas'}, {'id': 'F', 'kind': 'scatter:atlas'}, {'id': 'G', 'kind': 'scatter:atlas'}, {'id': 'H', 'kind': 'scatter:atlas'}, {'id': 'I', 'kind': 'scatter:atlas'}, {'id': 'J', 'kind': 'scatter:atlas'}, {'id': 'K', 'kind': 'scatter:atlas'}, {'id': 'L', 'kind': 'scatter:atlas'}, {'id': 'M', 'kind': 'scatter:atlas'}, {'id': 'N', 'kind': 'scatter:atlas'}, {'id': 'O', 'kind': 'scatter:atlas'}, {'id': 'P', 'kind': 'scatter:atlas'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': '16 scatter and bubble variants arranged as an atlas'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
