"""Report PPT workflow dependencies and actionable install commands."""
import argparse, importlib.util, json, shutil, subprocess
from pathlib import Path

def version(cmd):
    try:
        cp=subprocess.run(cmd,text=True,capture_output=True,timeout=15)
        return cp.stdout.strip() or cp.stderr.strip()
    except Exception: return None
def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path); a=p.parse_args()
    bins={n:shutil.which(n) for n in ("node","npm","libreoffice","soffice","pdftoppm")}
    py={n:bool(importlib.util.find_spec(n)) for n in ("pptx","PIL","defusedxml","markitdown")}
    office={"powerpoint_com":False,"wps_com":False}
    if __import__("os").name=="nt":
        script="$ErrorActionPreference='Stop'; try{$x=New-Object -ComObject PowerPoint.Application;$x.Quit();'PowerPoint'}catch{}; try{$w=New-Object -ComObject KWPP.Application;$w.Quit();'WPS'}catch{}"
        out=subprocess.run(["powershell","-NoProfile","-Command",script],text=True,capture_output=True).stdout
        office={"powerpoint_com":"PowerPoint" in out,"wps_com":"WPS" in out}
    missing=[]
    if not bins["node"]: missing.append("Node.js: winget install OpenJS.NodeJS.LTS")
    if not bins["pdftoppm"]: missing.append("Poppler: install poppler-utils or a Windows Poppler build")
    if not (bins["libreoffice"] or bins["soffice"] or office["powerpoint_com"] or office["wps_com"]): missing.append("Renderer: install LibreOffice, PowerPoint, or WPS")
    for mod,pkg in {"pptx":"python-pptx","PIL":"Pillow","defusedxml":"defusedxml","markitdown":"markitdown[pptx]"}.items():
        if not py[mod]: missing.append(f"Python: pip install {pkg}")
    result={"status":"PASS" if not missing else "BLOCK","binaries":bins,"python_modules":py,"office":office,"versions":{"node":version(["node","--version"]) if bins["node"] else None},"install_actions":missing}
    raw=json.dumps(result,ensure_ascii=False,indent=2); print(raw)
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(raw+"\n",encoding="utf-8")
    return 0 if not missing else 2
if __name__=="__main__": raise SystemExit(main())
