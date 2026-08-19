# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.reference_library import ReferenceLibrary


REVIEW = {
    "final_size_inspected": True,
    "hierarchy": "pass",
    "panel_balance": "pass",
    "whitespace": "pass",
    "legend_footprint": "pass",
    "text_legibility": "pass",
    "reviewer": "packet test",
}


class VisualOptimizationPacketTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="afs_visual_packet_"))
        (self.root / "SKILL.md").write_text("# test skill\n", encoding="utf-8")
        self.before = self.root / "before.png"
        self.before.write_bytes(b"before raster")
        self.lib = ReferenceLibrary(root=self.root)
        source = self.root / "line-reference.png"
        source.write_bytes(b"reference raster")
        ref = self.lib.ingest(source, "LineTrend", metadata_override={
            "tags": ["direct-labels"], "layout": "1x2", "source": "packet-test"
        })
        self.ref = self.lib.review(ref.id, 4.5, REVIEW)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_packet_materializes_shortlist_contract_and_next_actions(self):
        from scripts.prepare_visual_optimization import prepare_packet

        packet = prepare_packet(
            before=self.before,
            figure_type="LineTrend",
            output_dir=self.root / "optimization-packet",
            skill_root=self.root,
            preferred_tags=["direct-labels"],
        )

        recommendation = json.loads(packet["recommendation"].read_text(encoding="utf-8"))
        contract = json.loads(packet["contract"].read_text(encoding="utf-8"))
        runbook = packet["runbook"].read_text(encoding="utf-8")

        self.assertEqual([item["id"] for item in recommendation["candidates"]], [self.ref.id])
        self.assertEqual(contract["reference_candidates"], [self.ref.id])
        self.assertEqual(contract["opened_reference_candidates"], [])
        self.assertEqual(contract["selected_reference"], None)
        self.assertEqual(contract["selected_reference_visual_grammar"]["connectors"], "not_present")
        self.assertIn("objects_material", contract["selected_reference_visual_grammar"])
        self.assertIn("visual grammar", runbook.lower())
        self.assertEqual(contract["art_direction"]["id"], "unselected")
        self.assertIn("Do not edit plotting source", runbook)
        self.assertIn(str(self.before), runbook)
        self.assertIn(str(self.ref.image_path), runbook)


if __name__ == "__main__":
    unittest.main(verbosity=2)
