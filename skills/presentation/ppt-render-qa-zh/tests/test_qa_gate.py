import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"build_qa_report.py"

class QaGateTests(unittest.TestCase):
    def test_missing_manual_review_cannot_pass(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            for name,data in {"render":{"backend":"test","slide_count":3},"text":{},"geometry":{},"images":{}}.items():
                (td/f"{name}.json").write_text(json.dumps(data),encoding="utf-8")
            cp=subprocess.run([sys.executable,str(SCRIPT),"--render",str(td/"render.json"),"--text",str(td/"text.json"),"--geometry",str(td/"geometry.json"),"--images",str(td/"images.json"),"--output",str(td/"qa.md"),"--fix-log",str(td/"fix.md")],text=True,capture_output=True)
            self.assertNotEqual(cp.returncode,0)
            self.assertIn("CAUTION",(td/"qa.md").read_text(encoding="utf-8"))

    def test_completed_manual_review_allows_pass(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            for name,data in {"render":{"backend":"test","slide_count":3},"text":{},"geometry":{},"images":{}}.items():
                (td/f"{name}.json").write_text(json.dumps(data),encoding="utf-8")
            manual={"reviewer":"QA","checks":{"montage_rhythm":True,"representative_pages":True,"font_and_clipping":True,"contrast":True,"chart_readability":True},"notes":"reviewed"}
            (td/"manual.json").write_text(json.dumps(manual),encoding="utf-8")
            cp=subprocess.run([sys.executable,str(SCRIPT),"--render",str(td/"render.json"),"--text",str(td/"text.json"),"--geometry",str(td/"geometry.json"),"--images",str(td/"images.json"),"--manual-review",str(td/"manual.json"),"--output",str(td/"qa.md"),"--fix-log",str(td/"fix.md")],text=True,capture_output=True)
            self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)
            self.assertIn("**PASS**",(td/"qa.md").read_text(encoding="utf-8"))

if __name__ == "__main__": unittest.main()
