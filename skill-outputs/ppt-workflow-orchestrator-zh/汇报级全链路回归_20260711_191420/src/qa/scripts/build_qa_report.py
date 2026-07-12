"""Build a Markdown QA report from render and automated check manifests."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def load(path: Path): return json.loads(path.read_text(encoding="utf-8"))
def issues(data): return data.get("issues",[])+data.get("placeholder_hits",[])
def main() -> int:
    parser=argparse.ArgumentParser(description="Aggregate render, text, geometry and image QA into qa-report.md and fix-log.md.")
    for name in ("render","text","geometry","images","output","fix_log"): parser.add_argument(f"--{name.replace('_','-')}",dest=name,type=Path,required=True)
    parser.add_argument("--contract",type=Path,help="Optional Slide Contract/build bounds check JSON.")
    parser.add_argument("--manual-review",type=Path,help="Required for PASS; structured human review JSON.")
    parser.add_argument("--previous",type=Path)
    parser.add_argument("--extra",type=Path,action="append",default=[],help="Additional machine-check JSON; repeatable.")
    args=parser.parse_args(); render,text,geometry,images=map(load,(args.render,args.text,args.geometry,args.images)); current=issues(text)+issues(geometry)+issues(images)+(issues(load(args.contract)) if args.contract else [])+sum((issues(load(p)) for p in args.extra),[]); previous=issues(load(args.previous)) if args.previous else []
    blockers=[i for i in current if i.get("severity") in {"BLOCKER","ERROR"}]
    manual=load(args.manual_review) if args.manual_review and args.manual_review.is_file() else None
    required_manual=("montage_rhythm","representative_pages","font_and_clipping","contrast","chart_readability")
    manual_complete=bool(manual and manual.get("reviewer") and all(manual.get("checks",{}).get(k) is True for k in required_manual))
    status="BLOCK" if blockers else "CAUTION" if current or not manual_complete else "PASS"
    lines=["# PPT QA 报告","",f"- 结论：**{status}**",f"- 渲染后端：`{render.get('backend')}`",f"- 页数：{render.get('slide_count')}",f"- 当前自动问题：{len(current)}",f"- 前序问题：{len(previous)}","","## 当前问题","", "| 严重度 | 页 | 问题 |", "|---|---:|---|"]
    lines += [f"| {i.get('severity','ERROR')} | {i.get('slide',i.get('slide_id',''))} | {i.get('message',i.get('text',''))} |" for i in current] or ["| - | - | 无自动阻断项；仍需人工视觉检查 |"]
    checks=(manual or {}).get("checks",{})
    lines += ["","## 人工视觉检查","",f"- 审核人：{(manual or {}).get('reviewer','未填写')}"]
    labels={"montage_rhythm":"Montage 跨页节奏","representative_pages":"代表页逐页检查","font_and_clipping":"字体替换、遮挡与裁切","contrast":"文本与图形对比度","chart_readability":"图表可读性与口径"}
    lines += [f"- [{'x' if checks.get(k) is True else ' '}] {labels[k]}" for k in required_manual]
    lines += ["","## 结论边界","","自动检查不能证明不存在视觉问题；人工检查未结构化完成时结论最多为 CAUTION。"]
    output=args.output.resolve(); output.parent.mkdir(parents=True,exist_ok=True); output.write_text("\n".join(lines)+"\n",encoding="utf-8")
    fixed=max(0,len(previous)-len(current)); fix=["# 修复记录","",f"- 前序问题数：{len(previous)}",f"- 当前问题数：{len(current)}",f"- 自动推定已消除：{fixed}","","## 实际修复","","- 请填写问题、源文件修改、重新构建命令和复验结果。"]
    fix_path=args.fix_log.resolve(); fix_path.parent.mkdir(parents=True,exist_ok=True); fix_path.write_text("\n".join(fix)+"\n",encoding="utf-8"); print(json.dumps({"status":status,"report":str(output),"fix_log":str(fix_path)},ensure_ascii=False)); return 0 if status=="PASS" else 2

if __name__=="__main__": raise SystemExit(main())
