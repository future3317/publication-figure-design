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

SPEC = {'source_fingerprint': 'e805fb0f7ccdf8aa3ae764e8156cf6b61b6d56ef7dded0fc7556566e316649a3', 'width': 5400, 'height': 1800, 'visual_family': 'mechanism_schematic', 'observable_visual_grammar': {'panel_grid': [1, 3], 'panel_count': 3, 'aspect_class': 'wide', 'density': 'medium', 'visual_family': 'mechanism_schematic'}, 'reconstruction_blueprint': {'blueprint_id': 'dispersion_idea', 'mosaic': ['AABB'], 'panel_recipes': [{'id': 'A', 'kind': 'schematic:idea'}, {'id': 'B', 'kind': 'diagram:geometry'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'conceptual idea paired with geometric explanation'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
