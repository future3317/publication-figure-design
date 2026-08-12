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

SPEC = {'source_fingerprint': '999edb06b942f988a51b11f947845e42e4c346b2f9e5d5a6425def9e43bb69d1', 'width': 1600, 'height': 1367, 'visual_family': 'single_cell_systems', 'observable_visual_grammar': {'panel_grid': [3, 4], 'panel_count': 12, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'single_cell_systems'}, 'renderer_version': 2}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
