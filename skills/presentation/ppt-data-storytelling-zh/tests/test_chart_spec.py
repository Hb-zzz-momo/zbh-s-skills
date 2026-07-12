import csv, json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_chart_spec.py"

class ChartSpecTests(unittest.TestCase):
    def test_csv_is_aggregated_and_traceable(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); src=td/"data.csv"; out=td/"chart.json"
            with src.open("w", newline="", encoding="utf-8") as f:
                w=csv.writer(f); w.writerow(["quarter","value"]); w.writerows([["Q1",10],["Q1",5],["Q2",20]])
            cp=subprocess.run([sys.executable,str(SCRIPT),"--input",str(src),"--category","quarter","--value","value","--aggregate","sum","--title","季度结果","--unit","%","--source-id","SRC-DATA","--output",str(out)],text=True,capture_output=True)
            self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)
            data=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["series"][0]["values"],[15.0,20.0])
            self.assertEqual(data["provenance"]["source_id"],"SRC-DATA")

if __name__ == "__main__": unittest.main()
