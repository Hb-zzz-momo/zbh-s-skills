"""Use PowerPoint COM to measure actual text bounds and resolved fonts."""
import argparse, base64, json, os, subprocess
from pathlib import Path
def main():
    p=argparse.ArgumentParser(); p.add_argument("pptx",type=Path); p.add_argument("--output",type=Path,required=True); p.add_argument("--expected-font",action="append",default=[]); a=p.parse_args();
    if os.name!="nt":
        result={"status":"CAUTION","backend":"unavailable","issues":[{"severity":"WARNING","message":"PowerPoint COM is Windows-only"}]}; a.output.write_text(json.dumps(result,indent=2),encoding="utf-8"); return 0
    deck=str(a.pptx.resolve()).replace("'","''"); fonts="@("+",".join("'"+f.replace("'","''")+"'" for f in a.expected_font)+")"
    ps=f"""$ErrorActionPreference='Stop';$issues=@();$fonts=@{{}};$app=New-Object -ComObject PowerPoint.Application;$app.Visible=-1;$p=$app.Presentations.Open('{deck}',$true,$true,$false);foreach($s in $p.Slides){{foreach($sh in $s.Shapes){{try{{if($sh.HasTextFrame -and $sh.TextFrame2.HasText){{$t=$sh.TextFrame2.TextRange;$bw=$t.BoundWidth;$bh=$t.BoundHeight;if($bw -gt $sh.Width+1 -or $bh -gt $sh.Height+1){{$issues+=@{{severity='ERROR';slide=$s.SlideIndex;shape=$sh.Id;message='text_overflow';bound_width=$bw;bound_height=$bh;shape_width=$sh.Width;shape_height=$sh.Height}}}};$name=$t.Font.Name;if($name){{$fonts[$name]=1}}}}}}catch{{}}}}}};$p.Close();$app.Quit();[pscustomobject]@{{status=if($issues.Count){{'BLOCK'}}else{{'PASS'}};backend='PowerPoint COM';fonts=@($fonts.Keys);issues=$issues}}|ConvertTo-Json -Depth 8 -Compress"""
    enc=base64.b64encode(ps.encode("utf-16le")).decode(); cp=subprocess.run(["powershell","-NoProfile","-EncodedCommand",enc],text=True,capture_output=True)
    if cp.returncode:
        raise SystemExit(cp.stderr)
    result=json.loads(cp.stdout.strip())
    allowed=set(a.expected_font)
    if allowed:
        for font in result.get("fonts",[]):
            if font not in allowed: result["issues"].append({"severity":"WARNING","message":"unexpected_resolved_font","font":font})
        if result["issues"] and result["status"]=="PASS": result["status"]="CAUTION"
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,ensure_ascii=False)); return 2 if result["status"]=="BLOCK" else 0
if __name__=="__main__": raise SystemExit(main())
