import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ppt_workflow.py"
VALIDATE = ROOT / "scripts" / "validate_contract.py"
DELIVERY = ROOT / "scripts" / "validate_delivery.py"


class WorkflowTests(unittest.TestCase):
    def run_cli(self, *args, ok=True):
        cp = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], text=True, capture_output=True)
        if ok and cp.returncode:
            self.fail(cp.stdout + cp.stderr)
        return cp

    def test_vertical_slice_blocks_full_build_until_review_passes(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "deck"
            self.run_cli("init", "--project", project, "--mode", "from-scratch")
            state = json.loads((project / "workflow-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["current_stage"], "intake")
            state["current_stage"] = "vertical-slice"
            (project / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")
            (project / "slice").mkdir()
            (project / "slice" / "presentation-slice.pptx").write_bytes(b"pptx")
            (project / "slice" / "montage.png").write_bytes(b"png")
            (project / "slice" / "manual-review.json").write_text(json.dumps({"approved": False, "checks": {"visual": False}}), encoding="utf-8")
            blocked = self.run_cli("advance", "--project", project, "--to", "full-build", ok=False)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("vertical-slice", blocked.stderr)

    def test_all_four_primary_modes_initialize(self):
        with tempfile.TemporaryDirectory() as td:
            for mode in ("planning-only","from-scratch","from-template","edit-existing"):
                project=Path(td)/mode; self.run_cli("init","--project",project,"--mode",mode)
                state=json.loads((project/"workflow-state.json").read_text(encoding="utf-8")); self.assertEqual(state["mode"],mode)

    def test_contract_rejects_unknown_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            spec = {"deck": {"title": "x", "target_slides": 1}, "slides": [{
                "slide_id":"S01","section":"x","purpose":"x","audience_takeaway":"x","claim":"x",
                "evidence_refs":["SRC-404"],"visual_type":"hero","layout_family":"hero","dominant_asset":None,
                "content_blocks":[],"text_budget":{"title":18,"body":20,"footer":10},"source_footer":["SRC-404"],
                "speaker_notes":"x","qa_checks":["x"]}]}
            sources = {"sources": [{"source_id": "SRC-001", "title": "known"}]}
            (td/"spec.json").write_text(json.dumps(spec), encoding="utf-8")
            (td/"sources.json").write_text(json.dumps(sources), encoding="utf-8")
            cp = subprocess.run([sys.executable, str(VALIDATE), "--spec", str(td/"spec.json"), "--sources", str(td/"sources.json")], text=True, capture_output=True)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("SRC-404", cp.stdout)

    def test_contract_accepts_markdown_source_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); spec={"deck":{"target_slides":1},"slides":[{"slide_id":"S01","section":"x","purpose":"x","audience_takeaway":"x","claim":"x","evidence_refs":["SRC-001"],"visual_type":"hero","layout_family":"hero","dominant_asset":None,"content_blocks":[],"text_budget":{"title":5,"body":5,"footer":10},"source_footer":["SRC-001"],"speaker_notes":"x","qa_checks":["x"]}]}
            (td/"spec.json").write_text(json.dumps(spec),encoding="utf-8"); (td/"sources.md").write_text("| ID | 来源 |\n|---|---|\n| SRC-001 | 本地计划 |\n",encoding="utf-8")
            cp=subprocess.run([sys.executable,str(VALIDATE),"--spec",str(td/"spec.json"),"--sources",str(td/"sources.md")],text=True,capture_output=True)
            self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)

    def test_ship_rejects_block_qa_report(self):
        with tempfile.TemporaryDirectory() as td:
            project=Path(td); (project/"qa/pass2").mkdir(parents=True)
            (project/"workflow-state.json").write_text(json.dumps({"current_stage":"fix-loop","history":[]}),encoding="utf-8")
            (project/"qa/pass2/qa-report.md").write_text("- 结论：**BLOCK**",encoding="utf-8")
            (project/"qa/pass2/montage.png").write_bytes(b"png")
            cp=self.run_cli("advance","--project",project,"--to","ship",ok=False)
            self.assertNotEqual(cp.returncode,0); self.assertIn("must contain PASS",cp.stderr)

    def test_delivery_rejects_non_self_contained_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            cp=subprocess.run([sys.executable,str(DELIVERY),td,"--output",str(Path(td)/"manifest.json")],text=True,capture_output=True)
            self.assertNotEqual(cp.returncode,0); self.assertIn("missing required file",cp.stdout)


if __name__ == "__main__":
    unittest.main()
