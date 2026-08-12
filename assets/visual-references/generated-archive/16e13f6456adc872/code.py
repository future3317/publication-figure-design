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

SPEC = {'source_fingerprint': '4db30b32b65e6b7160ebe025993c2ffdaf6e240d836c253419e91649d3da8deb', 'width': 2700, 'height': 1200, 'visual_family': 'line_grid', 'observable_visual_grammar': {'panel_grid': [1, 2], 'panel_count': 2, 'aspect_class': 'wide', 'density': 'focused', 'visual_family': 'line_grid'}, 'renderer_version': 2}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
