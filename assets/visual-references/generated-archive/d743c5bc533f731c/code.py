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

SPEC = {'source_fingerprint': '854fe931bde6ca6c50eda6b147907f00d8f10d74c3b40bad1714b903bf945f00', 'width': 14400, 'height': 4800, 'visual_family': 'grouped_bar', 'observable_visual_grammar': {'panel_grid': [1, 3], 'panel_count': 3, 'aspect_class': 'wide', 'density': 'medium', 'visual_family': 'grouped_bar'}, 'renderer_version': 2}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
