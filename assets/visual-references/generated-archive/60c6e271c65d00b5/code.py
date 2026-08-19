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

SPEC = {'source_fingerprint': '3554b9af671886dfbbe985016440c5ba1633b4e8b08d50539d992982c5cc2bf5', 'width': 7200, 'height': 1800, 'visual_family': 'mechanism_schematic', 'observable_visual_grammar': {'panel_grid': [1, 2], 'panel_count': 2, 'aspect_class': 'wide', 'density': 'focused', 'visual_family': 'mechanism_schematic'}, 'reconstruction_blueprint': {'blueprint_id': 'vigil_concept', 'mosaic': ['AABB'], 'panel_recipes': [{'id': 'A', 'kind': 'schematic:temporal'}, {'id': 'B', 'kind': 'diagram:forecast'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'temporal concept sketch with forecast explanation'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
