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

SPEC = {'source_fingerprint': '2e0706fae3256e1de2388f8605f35b9b6ac23cfc397161a952f34cc5fa2f2192', 'width': 1600, 'height': 1419, 'visual_family': 'material_mechanism', 'observable_visual_grammar': {'panel_grid': [3, 4], 'panel_count': 12, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'material_mechanism'}, 'reconstruction_blueprint': {'blueprint_id': 'gallery_material_mechanism', 'mosaic': ['AABB', 'CDDE'], 'panel_recipes': [{'id': 'A', 'kind': 'schematic:materials'}, {'id': 'B', 'kind': 'diagram:mechanism'}, {'id': 'C', 'kind': 'spatial:micrograph'}, {'id': 'D', 'kind': 'line:response'}, {'id': 'E', 'kind': 'bar:comparison'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'asymmetric material mechanism figure with large mechanism hero'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
