import argparse,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser(); p.add_argument("--check",type=Path,action="append",required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); checks=[]; issues=[]
    for f in a.check:
        d=json.loads(f.read_text(encoding="utf-8")); checks.append({"file":str(f),"status":d.get("status")}); issues.extend(d.get("issues",[])+d.get("placeholder_hits",[]))
    blocked=any(c["status"] in {"BLOCK","FAIL"} for c in checks) or any(i.get("severity") in {"ERROR","BLOCKER"} for i in issues); result={"status":"BLOCK" if blocked else "PASS","checks":checks,"issues":issues}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,ensure_ascii=False)); return 2 if blocked else 0
if __name__=="__main__": raise SystemExit(main())
