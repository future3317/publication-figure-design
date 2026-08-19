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

SPEC = {'source_fingerprint': 'cd384abe10aa86bd310c1288a42f33735cb555c267bddae1ecd262905a7a1de5', 'width': 1500, 'height': 1183, 'visual_family': 'network_matrix', 'observable_visual_grammar': {'panel_grid': [4, 4], 'panel_count': 16, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'network_matrix'}, 'reconstruction_blueprint': {'blueprint_id': 'atlas_network_matrix', 'mosaic': ['ABCD', 'EFGH', 'IJKL', 'MNOP'], 'panel_recipes': [{'id': 'A', 'kind': 'network:atlas'}, {'id': 'B', 'kind': 'network:atlas'}, {'id': 'C', 'kind': 'network:atlas'}, {'id': 'D', 'kind': 'network:atlas'}, {'id': 'E', 'kind': 'network:atlas'}, {'id': 'F', 'kind': 'network:atlas'}, {'id': 'G', 'kind': 'network:atlas'}, {'id': 'H', 'kind': 'network:atlas'}, {'id': 'I', 'kind': 'network:atlas'}, {'id': 'J', 'kind': 'network:atlas'}, {'id': 'K', 'kind': 'network:atlas'}, {'id': 'L', 'kind': 'network:atlas'}, {'id': 'M', 'kind': 'network:atlas'}, {'id': 'N', 'kind': 'network:atlas'}, {'id': 'O', 'kind': 'network:atlas'}, {'id': 'P', 'kind': 'network:atlas'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': '16 network/matrix variants arranged as an atlas'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
