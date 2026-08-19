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

SPEC = {'source_fingerprint': '40dd7c7c14c45b45cc22ee23e19f2dc1901f38b26a1fb4b0f26a30dbd10c0423', 'width': 1500, 'height': 1156, 'visual_family': 'heatmap_grid', 'observable_visual_grammar': {'panel_grid': [4, 4], 'panel_count': 16, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'heatmap_grid'}, 'reconstruction_blueprint': {'blueprint_id': 'atlas_heatmaps', 'mosaic': ['ABCD', 'EFGH', 'IJKL', 'MNOP'], 'panel_recipes': [{'id': 'A', 'kind': 'heatmap:atlas'}, {'id': 'B', 'kind': 'heatmap:atlas'}, {'id': 'C', 'kind': 'heatmap:atlas'}, {'id': 'D', 'kind': 'heatmap:atlas'}, {'id': 'E', 'kind': 'heatmap:atlas'}, {'id': 'F', 'kind': 'heatmap:atlas'}, {'id': 'G', 'kind': 'heatmap:atlas'}, {'id': 'H', 'kind': 'heatmap:atlas'}, {'id': 'I', 'kind': 'heatmap:atlas'}, {'id': 'J', 'kind': 'heatmap:atlas'}, {'id': 'K', 'kind': 'heatmap:atlas'}, {'id': 'L', 'kind': 'heatmap:atlas'}, {'id': 'M', 'kind': 'heatmap:atlas'}, {'id': 'N', 'kind': 'heatmap:atlas'}, {'id': 'O', 'kind': 'heatmap:atlas'}, {'id': 'P', 'kind': 'heatmap:atlas'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': '16 matrix and annotation variants arranged as an atlas'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
