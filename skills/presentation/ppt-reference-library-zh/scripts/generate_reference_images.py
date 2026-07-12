from PIL import Image, ImageDraw, ImageFont
import argparse
from pathlib import Path
W,H=1600,900
def font(size,bold=False):
    paths=[Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),Path("C:/Windows/Fonts/arial.ttf")]
    for p in paths:
        if p.exists(): return ImageFont.truetype(str(p),size)
    return ImageFont.load_default()
def canvas(): return Image.new("RGB",(W,H),"#F7F4ED")
def save(img,p): img.save(p,optimize=True)
def title_good(p):
    im=canvas(); d=ImageDraw.Draw(im); d.rectangle((0,0,24,H),fill="#E05A47"); d.text((110,210),"把复杂问题讲成一个决定",font=font(68,True),fill="#172033"); d.text((115,330),"汇报对象 · 日期",font=font(28),fill="#5E6B7A"); d.ellipse((1170,170,1460,460),fill="#1B7F79"); save(im,p)
def title_bad(p):
    im=Image.new("RGB",(W,H),"#DDEBFF"); d=ImageDraw.Draw(im); colors=["#FF5B5B","#FFD43B","#4DABF7"]
    for i in range(9): d.rounded_rectangle((80+(i%3)*500,80+(i//3)*250,500+(i%3)*500,250+(i//3)*250),30,fill=colors[i%3]); d.text((105+(i%3)*500,130+(i//3)*250),"信息块",font=font(38,True),fill="#111111")
    d.text((330,380),"高端·科技·赋能·未来",font=font(64,True),fill="#FFFFFF"); save(im,p)
def data_good(p):
    im=canvas(); d=ImageDraw.Draw(im); d.text((90,55),"交付周期缩短 42%，拐点发生在第三阶段",font=font(50,True),fill="#172033"); base=760
    vals=[180,260,390,520]; labels=["Q1","Q2","Q3","Q4"]
    for i,v in enumerate(vals): x=170+i*310; d.rounded_rectangle((x,base-v,x+150,base),18,fill="#E05A47" if i==3 else "#1B7F79"); d.text((x+45,base+25),labels[i],font=font(26),fill="#5E6B7A")
    d.text((1180,240),"42%",font=font(90,True),fill="#E05A47"); d.text((1180,350),"关键改善",font=font(28),fill="#5E6B7A"); save(im,p)
def data_bad(p):
    im=Image.new("RGB",(W,H),"white"); d=ImageDraw.Draw(im); d.text((60,35),"数据分析",font=font(46,True),fill="black")
    for i in range(12):
        pts=[(100+j*120,780-(j*37+i*23)%600) for j in range(11)]; d.line(pts,fill=(20*i%255,90,230-12*i),width=5)
    for i in range(12): d.text((1050+(i%2)*240,100+(i//2)*70),f"系列 {i+1}",font=font(22),fill=(20*i%255,90,230-12*i)); save(im,p)
def process_good(p):
    im=canvas(); d=ImageDraw.Draw(im); d.text((90,55),"五个门禁把一次生成变成可验证闭环",font=font(50,True),fill="#172033")
    labs=["证据","叙事","设计","构建","复验"]
    for i,l in enumerate(labs): x=90+i*300; d.rounded_rectangle((x,350,x+220,510),24,fill="#E8F3F1",outline="#1B7F79",width=4); d.text((x+55,400),l,font=font(34,True),fill="#172033");
    for i in range(4): d.line((315+i*300,430,380+i*300,430),fill="#E05A47",width=8); d.polygon([(380+i*300,415),(405+i*300,430),(380+i*300,445)],fill="#E05A47")
    save(im,p)
def process_bad(p):
    im=canvas(); d=ImageDraw.Draw(im); d.text((90,40),"流程",font=font(48,True),fill="#172033")
    for i in range(18):
        x=70+(i%6)*250; y=150+(i//6)*230; d.ellipse((x,y,x+160,y+100),fill="#DDEBFF",outline="#4DABF7",width=3); d.text((x+35,y+32),f"步骤{i+1}",font=font(20),fill="#172033")
        if i<17: d.line((x+160,y+50,min(x+235,W-50),y+50),fill="#999999",width=3)
    save(im,p)
def main():
    p=argparse.ArgumentParser(); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=True)
    for name,fn in [("title-slide-good.png",title_good),("title-slide-bad.png",title_bad),("data-slide-good.png",data_good),("data-slide-bad.png",data_bad),("process-slide-good.png",process_good),("process-slide-bad.png",process_bad)]: fn(a.output_dir/name)
if __name__=="__main__": main()
