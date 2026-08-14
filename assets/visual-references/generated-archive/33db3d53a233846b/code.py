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

SPEC = {'source_fingerprint': '2ad2be6fa9c9165e800dba4d997850c9a426cbe9b441c78b76518335bcc3f948', 'width': 4200, 'height': 1800, 'visual_family': 'manifold_3d', 'observable_visual_grammar': {'panel_grid': [1, 2], 'panel_count': 2, 'aspect_class': 'wide', 'density': 'focused', 'visual_family': 'manifold_3d'}, 'reconstruction_blueprint': {'blueprint_id': 'rnagenscape_manifold_holes', 'mosaic': ['ABC'], 'panel_recipes': [{'id': 'A', 'kind': 'manifold:source'}, {'id': 'B', 'kind': 'manifold:holes'}, {'id': 'C', 'kind': 'manifold:generated'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'three manifold states emphasizing holes and generated coverage'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
