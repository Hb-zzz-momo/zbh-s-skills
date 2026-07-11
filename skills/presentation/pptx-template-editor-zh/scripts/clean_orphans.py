"""Report or remove media files not named in any OOXML relationship file."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    parser=argparse.ArgumentParser(description="Find unreferenced ppt/media files. Default is report-only; --apply deletes only reviewed candidates.")
    parser.add_argument("unpacked_dir",type=Path); parser.add_argument("--report",type=Path,required=True); parser.add_argument("--apply",action="store_true")
    args=parser.parse_args(); root=args.unpacked_dir.resolve(); media=root/"ppt"/"media"
    if not root.is_dir(): raise SystemExit(f"Unpacked directory not found: {root}")
    rel_text="\n".join(p.read_text(encoding="utf-8",errors="ignore") for p in root.rglob("*.rels"))
    candidates=[p for p in media.glob("*") if p.is_file() and p.name not in rel_text] if media.is_dir() else []
    deleted=[]
    if args.apply:
        for file in candidates: file.unlink(); deleted.append(str(file.relative_to(root)))
    result={"mode":"apply" if args.apply else "report-only","candidates":[str(p.relative_to(root)) for p in candidates],"deleted":deleted,"warning":"Review candidates before --apply; this tool never edits relationship XML."}
    report=args.report.resolve(); report.parent.mkdir(parents=True,exist_ok=True); report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(result,ensure_ascii=False)); return 0

if __name__ == "__main__": raise SystemExit(main())

