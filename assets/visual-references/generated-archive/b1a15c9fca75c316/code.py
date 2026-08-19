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

SPEC = {'source_fingerprint': '3373085ababf07481a352fe542fd79a58701e0e052c5593ca56984008ddad027', 'width': 3900, 'height': 3900, 'visual_family': 'grouped_bar', 'observable_visual_grammar': {'panel_grid': [1, 1], 'panel_count': 1, 'aspect_class': 'balanced', 'density': 'focused', 'visual_family': 'grouped_bar'}, 'reconstruction_blueprint': {'blueprint_id': 'cellsplicenet_ablation', 'mosaic': ['AAB', 'CCD'], 'panel_recipes': [{'id': 'A', 'kind': 'bar:ablation'}, {'id': 'B', 'kind': 'line:training'}, {'id': 'C', 'kind': 'distribution:violin'}, {'id': 'D', 'kind': 'table:metrics'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'ablation hero panel supported by training, distribution, and metric panels'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
