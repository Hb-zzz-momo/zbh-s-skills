"""Render PPTX to PDF and slide images through an available real Office backend."""
from __future__ import annotations
import argparse, base64, json, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

def ps_quote(value: Path) -> str: return "'" + str(value).replace("'", "''") + "'"

def render_com(source: Path, pdf: Path, prog_id: str) -> None:
    script=f"""$ErrorActionPreference='Stop'
$app=New-Object -ComObject {prog_id}
try {{
  $presentation=$app.Presentations.Open({ps_quote(source)}, $true, $true, $false)
  try {{ $presentation.SaveAs({ps_quote(pdf)}, 32) }} finally {{ $presentation.Close() }}
}} finally {{ $app.Quit(); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($app) | Out-Null }}
"""
    encoded=base64.b64encode(script.encode("utf-16le")).decode("ascii")
    subprocess.run(["powershell","-NoProfile","-NonInteractive","-EncodedCommand",encoded],check=True,capture_output=True,text=True)

def render_pdf(source: Path, out_dir: Path, backend: str) -> tuple[Path,str]:
    pdf=out_dir/(source.stem+".pdf")
    if pdf.exists(): pdf.unlink()
    if backend in {"auto","libreoffice"}:
        office=shutil.which("libreoffice") or shutil.which("soffice")
        if office:
            subprocess.run([office,"--headless","--convert-to","pdf","--outdir",str(out_dir),str(source)],check=True)
            if pdf.exists(): return pdf,"libreoffice"
        elif backend=="libreoffice": raise RuntimeError("LibreOffice/soffice not found. Install LibreOffice and add it to PATH.")
    if sys.platform=="win32" and backend in {"auto","powerpoint"}:
        try: render_com(source,pdf,"PowerPoint.Application"); return pdf,"powerpoint-com"
        except Exception:
            if backend=="powerpoint": raise
    if sys.platform=="win32" and backend in {"auto","wps"}:
        try: render_com(source,pdf,"KWPP.Application"); return pdf,"wps-com"
        except Exception:
            if backend=="wps": raise
    raise RuntimeError("No PPTX renderer available. Install LibreOffice, Microsoft PowerPoint, or WPS Office.")

def main() -> int:
    parser=argparse.ArgumentParser(description="Render PPTX to PDF and PNG slides using LibreOffice, PowerPoint COM or WPS COM.")
    parser.add_argument("pptx",type=Path); parser.add_argument("output_dir",type=Path); parser.add_argument("--backend",choices=["auto","libreoffice","powerpoint","wps"],default="auto"); parser.add_argument("--dpi",type=int,default=150)
    args=parser.parse_args(); source=args.pptx.resolve(); out=args.output_dir.resolve()
    if not source.is_file(): raise SystemExit(f"PPTX not found: {source}")
    out.mkdir(parents=True,exist_ok=True); pdf,used=render_pdf(source,out,args.backend)
    pdftoppm=shutil.which("pdftoppm")
    if not pdftoppm: raise SystemExit("pdftoppm not found. Install Poppler and add it to PATH.")
    slides=out/"slides"; slides.mkdir(exist_ok=True)
    for stale in slides.glob("slide-*.png"): stale.unlink()
    prefix=slides/"slide"
    subprocess.run([pdftoppm,"-png","-r",str(args.dpi),str(pdf),str(prefix)],check=True)
    images=sorted(slides.glob("slide-*.png"));
    if not images: raise SystemExit("PDF rendered but no slide images were created.")
    manifest={"source":str(source),"pdf":str(pdf),"backend":used,"dpi":args.dpi,"rendered_at":datetime.now(timezone.utc).isoformat(),"slide_count":len(images),"slides":[str(p) for p in images]}
    manifest_path=out/"render-manifest.json"; manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(manifest,ensure_ascii=False)); return 0

if __name__=="__main__": raise SystemExit(main())
