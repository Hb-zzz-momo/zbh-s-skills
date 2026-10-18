"""Build a traceable native-chart specification from CSV data."""
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import OrderedDict
from pathlib import Path

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",type=Path,required=True); p.add_argument("--category",required=True); p.add_argument("--value",required=True); p.add_argument("--series"); p.add_argument("--aggregate",choices=("sum","mean","min","max","none"),default="sum"); p.add_argument("--title",required=True); p.add_argument("--unit",default=""); p.add_argument("--source-id",required=True); p.add_argument("--chart-type",choices=("bar","column","line","area","pie"),default="column"); p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(); raw=a.input.read_bytes(); rows=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    if not rows or a.category not in rows[0] or a.value not in rows[0] or (a.series and a.series not in rows[0]): raise SystemExit("input fields are missing")
    categories=[]; groups=OrderedDict()
    for row in rows:
        cat=row[a.category]; ser=row[a.series] if a.series else a.title
        if cat not in categories: categories.append(cat)
        groups.setdefault(ser,OrderedDict()).setdefault(cat,[]).append(float(row[a.value]))
    def agg(v): return {"sum":sum,"mean":lambda x:sum(x)/len(x),"min":min,"max":max,"none":lambda x:x[0]}[a.aggregate](v)
    series=[{"name":name,"values":[round(float(agg(vals.get(cat,[0]))),6) for cat in categories]} for name,vals in groups.items()]
    result={"schema_version":1,"title":a.title,"chart_type":a.chart_type,"categories":categories,"series":series,"unit":a.unit,"axis":{"value_format":f"0{a.unit}" if a.unit else "0","zero_baseline":a.chart_type in {"bar","column"}},"provenance":{"source_id":a.source_id,"input":str(a.input.resolve()),"sha256":hashlib.sha256(raw).hexdigest(),"category_field":a.category,"value_field":a.value,"series_field":a.series,"aggregate":a.aggregate,"row_count":len(rows)}}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(a.output); return 0
if __name__=="__main__": raise SystemExit(main())
