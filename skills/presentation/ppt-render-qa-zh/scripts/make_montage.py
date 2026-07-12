"""Create a labeled slide montage from rendered images."""
from __future__ import annotations
import argparse, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def main() -> int:
    parser=argparse.ArgumentParser(description="Create a labeled PNG montage from slide PNG/JPG images.")
    parser.add_argument("slides_dir",type=Path); parser.add_argument("output",type=Path); parser.add_argument("--columns",type=int,default=3); parser.add_argument("--thumb-width",type=int,default=480)
    args=parser.parse_args(); root=args.slides_dir.resolve(); files=sorted([*root.glob("*.png"),*root.glob("*.jpg"),*root.glob("*.jpeg")])
    if not files: raise SystemExit(f"No slide images found in {root}")
    columns=max(1,args.columns); thumbs=[]
    for file in files:
        image=Image.open(file).convert("RGB"); height=round(image.height*args.thumb_width/image.width); thumbs.append(image.resize((args.thumb_width,height),Image.Resampling.LANCZOS))
    cell_h=max(i.height for i in thumbs)+42; rows=math.ceil(len(thumbs)/columns); canvas=Image.new("RGB",(columns*(args.thumb_width+24)+24,rows*(cell_h+24)+24),"#ECECEC"); draw=ImageDraw.Draw(canvas); font=ImageFont.load_default()
    for index,image in enumerate(thumbs):
        x=24+(index%columns)*(args.thumb_width+24); y=24+(index//columns)*(cell_h+24); canvas.paste(image,(x,y)); draw.text((x,y+image.height+10),f"Slide {index+1}",fill="#202020",font=font)
    output=args.output.resolve(); output.parent.mkdir(parents=True,exist_ok=True); canvas.save(output); print(output); return 0

if __name__=="__main__": raise SystemExit(main())
