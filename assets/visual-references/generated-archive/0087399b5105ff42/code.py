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

SPEC = {'source_fingerprint': '9f02fa4603dae748e3745b95b0ed252f2ba386da6101dc1be6c4a2a886c78eb0', 'width': 5313, 'height': 3000, 'visual_family': 'manifold_3d', 'observable_visual_grammar': {'panel_grid': [1, 2], 'panel_count': 2, 'aspect_class': 'wide', 'density': 'focused', 'visual_family': 'manifold_3d'}, 'reconstruction_blueprint': {'blueprint_id': 'cflows_diffusion_swiss_roll', 'mosaic': ['AABB'], 'panel_recipes': [{'id': 'A', 'kind': 'manifold:source'}, {'id': 'B', 'kind': 'manifold:flow'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'paired manifold views showing source geometry and transformed geometry'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
