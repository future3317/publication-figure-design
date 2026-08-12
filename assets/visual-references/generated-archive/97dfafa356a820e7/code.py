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

SPEC = {'source_fingerprint': 'f1f564e0c7221f24f4bffe14cce5b5df6786c75f7dfcf1b6d2be7566820050ec', 'width': 2124, 'height': 1588, 'visual_family': 'comparison_composite', 'observable_visual_grammar': {'panel_grid': [3, 4], 'panel_count': 12, 'aspect_class': 'balanced', 'density': 'high', 'visual_family': 'comparison_composite'}, 'renderer_version': 2}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
