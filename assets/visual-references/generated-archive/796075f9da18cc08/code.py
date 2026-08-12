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

SPEC = {'source_fingerprint': 'e7fa7d98cd4f5263f5550d7ac8824e60071c20b2927aef52ac6d18d62fd29ffa', 'width': 1500, 'height': 1216, 'visual_family': 'radar_grid', 'observable_visual_grammar': {'panel_grid': [4, 4], 'panel_count': 16, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'radar_grid'}, 'renderer_version': 2}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
