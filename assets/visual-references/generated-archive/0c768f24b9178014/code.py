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

SPEC = {'source_fingerprint': '59846b700abcf89c2779abce27b5d667637f6429cf4a52ca1892c687359f2aa7', 'width': 2928, 'height': 1012, 'visual_family': 'comparison_composite', 'observable_visual_grammar': {'panel_grid': [3, 4], 'panel_count': 12, 'aspect_class': 'wide', 'density': 'high', 'visual_family': 'comparison_composite'}, 'reconstruction_blueprint': {'blueprint_id': 'dispersion_observation', 'mosaic': ['AABB', 'CCDD', 'EEFF'], 'panel_recipes': [{'id': 'A', 'kind': 'schematic:observation'}, {'id': 'B', 'kind': 'scatter:groups'}, {'id': 'C', 'kind': 'heatmap:correlation'}, {'id': 'D', 'kind': 'line:comparison'}, {'id': 'E', 'kind': 'distribution:ridge'}, {'id': 'F', 'kind': 'forest:effects'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'asymmetric observation figure with one explanatory panel and five evidence panels'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
