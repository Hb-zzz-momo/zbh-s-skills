import argparse, json, statistics
from pathlib import Path
def main():
    p=argparse.ArgumentParser(); p.add_argument("--spec",type=Path,required=True); p.add_argument("--minutes",type=float,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); data=json.loads(a.spec.read_text(encoding="utf-8")); slides=data.get("slides",[]); issues=[]; rows=[]
    if not slides: raise SystemExit("slides missing")
    weights=[]
    for s in slides:
        notes=str(s.get("speaker_notes","")).strip(); w=max(20,len(notes))
        if not notes: issues.append({"severity":"ERROR","slide_id":s.get("slide_id"),"message":"missing speaker_notes"})
        weights.append(w)
    total=a.minutes*60
    for s,w in zip(slides,weights): rows.append({"slide_id":s.get("slide_id"),"section":s.get("section"),"seconds":round(total*w/sum(weights),1),"notes":s.get("speaker_notes","")})
    med=statistics.median(r["seconds"] for r in rows)
    for r in rows:
        if r["seconds"]>med*2.5: issues.append({"severity":"WARNING","slide_id":r["slide_id"],"message":"timing spike"})
    status="BLOCK" if any(i["severity"]=="ERROR" for i in issues) else "CAUTION" if issues else "PASS"; result={"status":status,"target_seconds":total,"allocated_seconds":round(sum(r["seconds"] for r in rows),1),"slides":rows,"issues":issues}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,ensure_ascii=False)); return 2 if status=="BLOCK" else 0
if __name__=="__main__": raise SystemExit(main())
