from PIL import Image, ImageChops, ImageStat
from math import sqrt
import argparse, json
from pathlib import Path
def main():
    p=argparse.ArgumentParser(); p.add_argument("baseline",type=Path); p.add_argument("candidate",type=Path); p.add_argument("--output",type=Path,required=True); p.add_argument("--max-rms",type=float,default=8.0); p.add_argument("--background",default="FFFFFF"); a=p.parse_args()
    def flatten(path):
        im=Image.open(path).convert("RGBA"); bg=Image.new("RGBA",im.size,"#"+a.background); bg.alpha_composite(im); return bg.convert("RGB")
    x=flatten(a.baseline); y=flatten(a.candidate)
    if x.size!=y.size: result={"status":"BLOCK","issues":[{"severity":"ERROR","message":"image_size_changed","baseline":x.size,"candidate":y.size}]}
    else:
        channel_rms=ImageStat.Stat(ImageChops.difference(x,y)).rms; rms=sqrt(sum(v*v for v in channel_rms)/len(channel_rms)); result={"status":"PASS" if rms<=a.max_rms else "BLOCK","rms":rms,"channel_rms":channel_rms,"threshold":a.max_rms,"issues":[] if rms<=a.max_rms else [{"severity":"ERROR","message":"visual_regression","rms":rms}]}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result)); return 0 if result["status"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
