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

SPEC = {'source_fingerprint': '5da6979582203956d3f54535ea8286acaaaaba5d588066891ee037de056ed545', 'width': 3130, 'height': 1300, 'visual_family': 'mechanism_schematic', 'observable_visual_grammar': {'panel_grid': [2, 3], 'panel_count': 6, 'aspect_class': 'wide', 'density': 'medium', 'visual_family': 'mechanism_schematic'}, 'reconstruction_blueprint': {'blueprint_id': 'rnagenscape_schematic', 'mosaic': ['AABB', 'CCDD'], 'panel_recipes': [{'id': 'A', 'kind': 'schematic:generator'}, {'id': 'B', 'kind': 'diagram:conditioning'}, {'id': 'C', 'kind': 'manifold:latent'}, {'id': 'D', 'kind': 'spatial:expression'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'generative pipeline with latent-space and spatial readouts'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
