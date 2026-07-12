"""Validate and hash a self-contained PPT delivery bundle."""
import argparse, hashlib, json
from pathlib import Path
REQUIRED=("presentation.pptx","presentation.pdf","brief.md","sources.md","claim-evidence-map.md","storyline.md","slide-spec.json","PRESENTATION_DESIGN.md","qa-report.md","workflow-state.json","qa/pass1/qa-report.md","qa/fix-log.md","qa/pass2/qa-report.md","qa/pass2/montage.png","speaker-timing.json")
REQUIRED_DIRS=("assets","data","src")
def main():
    p=argparse.ArgumentParser(); p.add_argument("project",type=Path); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); root=a.project.resolve(); issues=[]
    for rel in REQUIRED:
        f=root/rel
        if not f.is_file() or f.stat().st_size==0: issues.append({"severity":"BLOCKER","message":"missing required file","path":rel})
    for rel in REQUIRED_DIRS:
        d=root/rel
        if not d.is_dir() or not any(x.is_file() for x in d.rglob("*")): issues.append({"severity":"BLOCKER","message":"missing or empty required directory","path":rel})
    try:
        state=json.loads((root/"workflow-state.json").read_text(encoding="utf-8"))
        if state.get("current_stage")!="ship": issues.append({"severity":"BLOCKER","message":"workflow has not reached ship"})
    except Exception: pass
    try:
        if "结论：**PASS**" not in (root/"qa/pass2/qa-report.md").read_text(encoding="utf-8"): issues.append({"severity":"BLOCKER","message":"pass2 QA is not PASS"})
    except Exception: pass
    files=[]
    output=a.output.resolve()
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.resolve()!=output: files.append({"path":f.relative_to(root).as_posix(),"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
    result={"status":"PASS" if not issues else "BLOCK","root":str(root),"file_count":len(files),"issues":issues,"files":files}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"status":result["status"],"file_count":len(files),"issues":issues},ensure_ascii=False)); return 0 if not issues else 2
if __name__=="__main__": raise SystemExit(main())
