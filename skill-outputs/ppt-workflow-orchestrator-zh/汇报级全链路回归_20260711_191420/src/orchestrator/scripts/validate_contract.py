"""Validate a slide contract against its evidence inventory."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

REQUIRED = ("slide_id","section","purpose","audience_takeaway","claim","evidence_refs","visual_type","layout_family","dominant_asset","content_blocks","text_budget","source_footer","speaker_notes","qa_checks")

def load(path: Path): return json.loads(path.read_text(encoding="utf-8"))
def load_sources(path: Path):
    text=path.read_text(encoding="utf-8-sig")
    if path.suffix.lower()==".json" or text.lstrip().startswith(("{","[")): return json.loads(text)
    ids=sorted(set(re.findall(r"\bSRC-[A-Za-z0-9_-]+\b",text)))
    if not ids: raise ValueError(f"no SRC-* identifiers found in Markdown source inventory: {path}")
    return {"sources":[{"source_id":source_id} for source_id in ids]}
def source_ids(data):
    rows = data.get("sources", data if isinstance(data, list) else [])
    return {str(r.get("source_id", r.get("id"))) for r in rows if isinstance(r, dict)}

def validate(spec: dict, sources: dict | None = None) -> list[dict]:
    issues=[]; slides=spec.get("slides")
    if not isinstance(slides,list) or not slides: return [{"severity":"BLOCKER","path":"slides","message":"slides must be a non-empty array"}]
    ids=[]; known=source_ids(sources or {})
    for i,slide in enumerate(slides):
        path=f"slides[{i}]"; ids.append(slide.get("slide_id"))
        for key in REQUIRED:
            if key not in slide: issues.append({"severity":"BLOCKER","path":f"{path}.{key}","message":f"missing required field: {key}"})
        budget=slide.get("text_budget",{})
        for key in ("title","body","footer"):
            if not isinstance(budget.get(key),int) or budget.get(key,0)<0: issues.append({"severity":"BLOCKER","path":f"{path}.text_budget.{key}","message":"text budget must be a non-negative integer"})
        title=str(slide.get("claim", slide.get("purpose",""))); body=" ".join(str(b.get("content",b.get("label",b.get("value","")))) for b in slide.get("content_blocks",[]) if isinstance(b,dict))
        if len(title)>budget.get("title",10**9): issues.append({"severity":"ERROR","path":path,"message":f"title exceeds budget: {len(title)} > {budget.get('title')}"})
        if len(body)>budget.get("body",10**9): issues.append({"severity":"ERROR","path":path,"message":f"body exceeds budget: {len(body)} > {budget.get('body')}"})
        if known:
            for ref in set(slide.get("evidence_refs",[])+slide.get("source_footer",[])):
                if ref not in known: issues.append({"severity":"BLOCKER","path":path,"message":f"unknown evidence reference: {ref}"})
    if len(set(ids)) != len(ids) or any(not x for x in ids): issues.append({"severity":"BLOCKER","path":"slides","message":"slide_id must be unique and non-empty"})
    target=spec.get("deck",{}).get("target_slides")
    if target is not None and target != len(slides): issues.append({"severity":"ERROR","path":"deck.target_slides","message":f"target_slides={target} but actual={len(slides)}"})
    return issues

def main():
    p=argparse.ArgumentParser(); p.add_argument("--spec",type=Path,required=True); p.add_argument("--sources",type=Path); p.add_argument("--output",type=Path)
    a=p.parse_args(); issues=validate(load(a.spec),load_sources(a.sources) if a.sources else None); result={"status":"PASS" if not issues else "BLOCK","issues":issues}
    raw=json.dumps(result,ensure_ascii=False,indent=2); print(raw)
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(raw+"\n",encoding="utf-8")
    return 0 if not issues else 2
if __name__=="__main__": raise SystemExit(main())
