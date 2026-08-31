# -*- coding: utf-8 -*-
"""Tests that adapter bundles stay in lockstep with the root manifest."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_adapters import _runtime_files


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.yaml"


class TestAdapterManifestLockstep(unittest.TestCase):
    def _root_runtime(self) -> list[str]:
        text = MANIFEST.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        return list(data.get("runtime", []))

    def test_helper_runtime_matches_root_manifest(self):
        self.assertEqual(_runtime_files(), self._root_runtime())

    def test_codex_manifest_runtime_matches_root(self):
        codex_manifest = ROOT / "install" / "codex" / "manifest.yaml"
        self.assertTrue(codex_manifest.is_file(), "codex manifest missing")
        data = yaml.safe_load(codex_manifest.read_text(encoding="utf-8"))
        self.assertEqual(list(data.get("runtime", [])), self._root_runtime())

    def test_codex_manifest_version_matches_root(self):
        root_data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        codex_data = yaml.safe_load(
            (ROOT / "install" / "codex" / "manifest.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(codex_data.get("version"), root_data.get("version"))

    def test_adapter_instructions_list_root_runtime(self):
        """Every adapter's loader header must enumerate the same runtime bundle."""
        runtime = self._root_runtime()
        runtime_lines = "\n".join(f"- `{item}`" for item in runtime)
        for name in ("claude-code", "cursor", "copilot"):
            with self.subTest(adapter=name):
                if name == "claude-code":
                    path = ROOT / "install" / name / "README.md"
                elif name == "cursor":
                    path = ROOT / "install" / name / ".cursorrules"
                else:
                    path = ROOT / "install" / name / "copilot-instructions.md"
                self.assertTrue(path.is_file(), f"{name} instructions missing")
                text = path.read_text(encoding="utf-8")
                self.assertIn("Runtime bundle:", text)
                for line in runtime_lines.splitlines():
                    self.assertIn(line, text)


if __name__ == "__main__":
    unittest.main()
