"""Executable PPT workflow state machine with hard stage gates."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

STAGES=("intake","evidence","narrative","slide-contract","visual-system","vertical-slice","full-build","render-qa","fix-loop","ship")
MODES=("planning-only","from-scratch","from-template","edit-existing")
REQUIRED={
 "evidence":("brief.md","material-inventory.md","missing-information.md"),
 "narrative":("sources.md","claim-evidence-map.md"),
 "slide-contract":("storyline.md",),
 "visual-system":("slide-spec.json",),
 "vertical-slice":("PRESENTATION_DESIGN.md",),
 "full-build":("slice/presentation-slice.pptx","slice/montage.png","slice/manual-review.json"),
 "render-qa":("presentation.pptx",),
 "fix-loop":("qa/pass1/qa-report.md","qa/fix-log.md"),
 "ship":("qa/pass2/qa-report.md","qa/pass2/montage.png"),
}

def state_path(project): return project/"workflow-state.json"
def load(project): return json.loads(state_path(project).read_text(encoding="utf-8"))
def save(project,state): state["updated_at"]=datetime.now(timezone.utc).isoformat(); state_path(project).write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def review_passed(path):
    try:
        d=json.loads(path.read_text(encoding="utf-8")); return bool(d.get("approved")) and all(d.get("checks",{}).values())
    except Exception: return False
def qa_passed(path):
    try: return "结论：**PASS**" in path.read_text(encoding="utf-8")
    except Exception: return False
def gate(project,target):
    missing=[p for p in REQUIRED.get(target,()) if not (project/p).is_file()]
    if target=="full-build" and not review_passed(project/"slice/manual-review.json"): missing.append("vertical-slice manual review approval")
    if target=="ship" and not qa_passed(project/"qa/pass2/qa-report.md"): missing.append("qa/pass2/qa-report.md must contain PASS")
    return missing
def init(a):
    a.project.mkdir(parents=True,exist_ok=True)
    if state_path(a.project).exists(): raise SystemExit("workflow-state.json already exists")
    state={"schema_version":1,"mode":a.mode,"current_stage":"intake","history":[{"stage":"intake","result":"PASS"}]}; save(a.project,state); print(state_path(a.project)); return 0
def advance(a):
    project=a.project.resolve(); state=load(project); current=STAGES.index(state["current_stage"]); target=STAGES.index(a.to)
    if target != current+1: raise SystemExit(f"must advance one stage at a time: {state['current_stage']} -> {STAGES[current+1] if current+1<len(STAGES) else 'done'}")
    missing=gate(project,a.to)
    if missing: raise SystemExit(f"gate BLOCK for {a.to}; missing: "+", ".join(missing))
    state["current_stage"]=a.to; state["history"].append({"stage":a.to,"result":"PASS"}); save(project,state); print(json.dumps(state,ensure_ascii=False)); return 0
def status(a): print(json.dumps(load(a.project.resolve()),ensure_ascii=False,indent=2)); return 0
def audit(a):
    project=a.project.resolve(); state=load(project)
    if state["current_stage"]=="ship":
        missing=gate(project,"ship")
        if missing:
            state["current_stage"]="fix-loop"; state["history"].append({"stage":"ship","result":"BLOCK","reason":"; ".join(missing)}); save(project,state); print(json.dumps(state,ensure_ascii=False)); return 2
    print(json.dumps(state,ensure_ascii=False)); return 0
def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    i=sub.add_parser("init"); i.add_argument("--project",type=Path,required=True); i.add_argument("--mode",choices=MODES,required=True); i.set_defaults(fn=init)
    a=sub.add_parser("advance"); a.add_argument("--project",type=Path,required=True); a.add_argument("--to",choices=STAGES[1:],required=True); a.set_defaults(fn=advance)
    s=sub.add_parser("status"); s.add_argument("--project",type=Path,required=True); s.set_defaults(fn=status)
    q=sub.add_parser("audit"); q.add_argument("--project",type=Path,required=True); q.set_defaults(fn=audit)
    args=p.parse_args(); return args.fn(args)
if __name__=="__main__": raise SystemExit(main())
