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

SPEC = {'source_fingerprint': '71133ed59cc16f8c36a4e8b2325575d185f36a8534c29579d2eff177544e9e53', 'width': 10800, 'height': 3600, 'visual_family': 'grouped_bar', 'observable_visual_grammar': {'panel_grid': [2, 4], 'panel_count': 8, 'aspect_class': 'wide', 'density': 'high', 'visual_family': 'grouped_bar'}, 'reconstruction_blueprint': {'blueprint_id': 'brainteaser_selfcorrection_math', 'mosaic': ['ABCD', 'EFGH'], 'panel_recipes': [{'id': 'A', 'kind': 'bar:category'}, {'id': 'B', 'kind': 'bar:category'}, {'id': 'C', 'kind': 'bar:category'}, {'id': 'D', 'kind': 'bar:category'}, {'id': 'E', 'kind': 'line:iterations'}, {'id': 'F', 'kind': 'scatter:paired'}, {'id': 'G', 'kind': 'distribution:points'}, {'id': 'H', 'kind': 'table:metrics'}], 'annotation_model': 'panel_letters + local_legends + direct_callouts', 'source_observation': 'dense self-correction grid: categorical gains, iterations, paired observations, and metrics'}, 'renderer_version': 3}

if __name__ == '__main__':
    render_from_spec(SPEC, Path(__file__).with_name('reproduced.png'))
