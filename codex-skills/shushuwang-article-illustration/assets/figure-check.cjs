// 模板：图片自检——手机等效字号、卡片溢出、柱状图数值与图形一致、标签是否压图形。放在 编辑记录/ 下，和 figures.html 同目录。
// 图片自检：换算到手机显示宽度后，字够不够大；柱状图和标签对不对得上；有没有越界。
const {chromium}=require('C:/Users/zbh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path=require('path');
const {pathToFileURL}=require('url');

const ROOT=path.resolve(__dirname,'..');
const PHONE=375;                     // 手机上图片按 375px 宽显示
const MIN_KEY=12;                    // 关键文字（标题/数字）手机等效字号下限
const MIN_SECONDARY=9;               // 说明性小字下限
const CARDS=[
  ['fig-cover','00-封面.png'],
  ['fig-01','01-改动.png'],
  ['fig-02','02-改动.png'],
  ['fig-03','03-公式卡.png'],
  ['fig-04','04-改动.png'],
  ['fig-05','05-自测卡.png'],
];

(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const page=await browser.newPage({viewport:{width:2600,height:1400}});
  await page.goto(pathToFileURL(path.join(__dirname,'figures.html')).href);
  await page.evaluate(()=>document.fonts.ready);

  let failed=0; const report=[];
  for(const [id,file] of CARDS){
    const el=page.locator('#'+id);
    const box=await el.boundingBox();
    const scale=PHONE/box.width;
    const info=await el.evaluate((node)=>{
      const out={texts:[],overflow:null,bars:[]};
      const walk=(n)=>{
        for(const c of n.childNodes){
          if(c.nodeType===3){
            const t=(c.textContent||'').trim();
            if(t && n.tagName!=='STYLE' && n.tagName!=='SCRIPT'){
              const fs=parseFloat(getComputedStyle(n).fontSize)||0;
              out.texts.push({t:t.slice(0,18),fs});
            }
          }else if(c.nodeType===1) walk(c);
        }
      };
      walk(node);
      out.overflow={sw:node.scrollWidth,cw:Math.round(node.getBoundingClientRect().width),
                    sh:node.scrollHeight,ch:Math.round(node.getBoundingClientRect().height)};
      const nb=node.getBoundingClientRect();
      out.widest=[...node.querySelectorAll('*')].map(e=>({t:e.tagName+'.'+String(e.className||'').slice(0,16),r:Math.round(e.getBoundingClientRect().right-nb.left)})).sort((a,b)=>b.r-a.r).slice(0,3);
      out.bars=[...node.querySelectorAll('svg rect')].map(r=>({y:+r.getAttribute('y'),h:+r.getAttribute('height')}));
      // 图片（含 logo）不得压住文字：块级盒子占满整行，必须用 Range 取真正着墨的文本框，否则误报。
      out.imgHits=[];
      const imgs=[...node.querySelectorAll('img')].map(i=>i.getBoundingClientRect());
      const leaves=[...node.querySelectorAll('*')]
        .filter(e=>e.children.length===0&&e.textContent.trim()&&!/^(style|script)$/i.test(e.tagName));
      for(const t of leaves){
        const range=document.createRange();
        range.selectNodeContents(t);
        for(const b of range.getClientRects()){
          for(const r of imgs){
            const ox=Math.min(b.right,r.right)-Math.max(b.left,r.left);
            const oy=Math.min(b.bottom,r.bottom)-Math.max(b.top,r.top);
            if(ox>2&&oy>2) out.imgHits.push(`图片压住文字「${t.textContent.trim().slice(0,14)}」`);
          }
        }
      }
      // 文字不得溢出它所在的那个“框”（有边框或底色的元素）——封面右侧面板就是这么漏过去的
      out.textOverflow=[];
      out.boxOverflow=[];
      const cardRect=node.getBoundingClientRect();
      const boxEls=[...node.querySelectorAll('*')].filter(e=>{
        const cs=getComputedStyle(e);
        const bw=['borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth']
          .some(k=>parseFloat(cs[k])>0);
        const bg=cs.backgroundColor&&!/rgba?\(0, 0, 0, 0\)/.test(cs.backgroundColor);
        return bw||bg;
      });
      for(const box of boxEls){
        const br=box.getBoundingClientRect();
        if(br.width<8||br.height<8) continue;
        for(const leaf of box.querySelectorAll('*')){
          if(leaf.children.length>0||!leaf.textContent.trim()) continue;
          if(/^(style|script)$/i.test(leaf.tagName)) continue;
          const rg=document.createRange();
          rg.selectNodeContents(leaf);
          for(const r of rg.getClientRects()){
            if(r.width===0||r.height===0) continue;
            const over=Math.max(br.left-r.left,r.right-br.right,br.top-r.top,r.bottom-br.bottom);
            if(over>1.5) out.textOverflow.push(`文字溢出所在框 ${Math.round(over)}px：「${leaf.textContent.trim().slice(0,14)}」`);
          }
        }
      }
      // 卡片有 overflow:hidden，越界元素会被悄悄裁掉，也要当失败
      for(const e of node.querySelectorAll('*')){
        const r=e.getBoundingClientRect();
        if(r.width===0&&r.height===0) continue;
        const over=Math.max(cardRect.left-r.left,r.right-cardRect.right,cardRect.top-r.top,r.bottom-cardRect.bottom);
        if(over>1.5) out.boxOverflow.push(`元素越出卡片 ${Math.round(over)}px：${e.tagName}.${String(e.className||'').slice(0,14)}`);
      }
      // 贴图不得盖住任何“边框线”（相框、表格线、分割线……）。
      // 只比边框那四条带，不能比元素整块矩形——相框内部是空的，比整块会误报。
      out.imgOverBorder=[];
      const bwOf=(cs)=>({t:parseFloat(cs.borderTopWidth)||0,r:parseFloat(cs.borderRightWidth)||0,
        b:parseFloat(cs.borderBottomWidth)||0,l:parseFloat(cs.borderLeftWidth)||0});
      const bordered=[...node.querySelectorAll('*')].filter(e=>{
        const w=bwOf(getComputedStyle(e));
        return w.t||w.r||w.b||w.l;
      });
      for(const im of node.querySelectorAll('img')){
        const ir=im.getBoundingClientRect();
        if(ir.width<4||ir.height<4) continue;
        let hit=null;
        for(const b of bordered){
          if(b===im) continue;
          const br=b.getBoundingClientRect();
          const w=bwOf(getComputedStyle(b));
          const strips=[
            {l:br.left,t:br.top,r:br.right,b:br.top+w.t},
            {l:br.left,t:br.bottom-w.b,r:br.right,b:br.bottom},
            {l:br.left,t:br.top,r:br.left+w.l,b:br.bottom},
            {l:br.right-w.r,t:br.top,r:br.right,b:br.bottom},
          ];
          for(const s of strips){
            if(s.r-s.l<=0||s.b-s.t<=0) continue;
            const ox=Math.min(ir.right,s.r)-Math.max(ir.left,s.l);
            const oy=Math.min(ir.bottom,s.b)-Math.max(ir.top,s.t);
            if(ox>1&&oy>1){ hit=`${Math.round(ox)}×${Math.round(oy)}px：${b.tagName}.${String(b.className||'').slice(0,16)}`; break; }
          }
          if(hit) break;
        }
        if(hit) out.imgOverBorder.push(`贴图盖住边框 ${hit}`);
      }
      return out;
    }, null);
    const equiv=(fs)=>+(fs*scale).toFixed(1);
    const sizes=info.texts.map(t=>equiv(t.fs));
    const minKey=Math.min(...info.texts.filter(t=>t.fs>=34).map(t=>equiv(t.fs)), 99);
    const minAny=Math.min(...sizes, 99);
    const probs=[];
    if(info.overflow.sw>info.overflow.cw+1||info.overflow.sh>info.overflow.ch+1) probs.push(`内容溢出卡片 sw=${info.overflow.sw} cw=${info.overflow.cw} sh=${info.overflow.sh} ch=${info.overflow.ch}`);
    if(minKey<MIN_KEY) probs.push(`关键文字手机等效 ${minKey}px < ${MIN_KEY}px`);
    if(minAny<MIN_SECONDARY) probs.push(`最小文字手机等效 ${minAny}px < ${MIN_SECONDARY}px`);
    const smallest=[...info.texts].sort((a,b)=>equiv(a.fs)-equiv(b.fs)).slice(0,3).map(t=>`${equiv(t.fs)}px「${t.t}」`);
    // SVG 内部元素越界 + 文字压图形 / 文字互压（无 SVG 的卡片自动跳过）
    const svgProbs=await el.evaluate((node)=>{
      const out=[];
      for(const svg of node.querySelectorAll('svg')){
        const vb=svg.viewBox.baseVal;
        const rect=svg.getBoundingClientRect();
        const toCard=(b)=>({l:b.left-rect.left,r:b.right-rect.left,t:b.top-rect.top,b:b.bottom-rect.top});
        const vis=[]; const txt=[];
        for(const c of svg.querySelectorAll('rect,line,polyline,circle,text')){
          const bb=c.getBoundingClientRect();
          if(bb.width===0&&bb.height===0) continue;
          const k=toCard(bb);
          if(k.l<-1||k.r>rect.width+1||k.t<-1||k.b>rect.height+1){
            out.push(`越界：${c.tagName}「${(c.textContent||'').slice(0,12)}」`);
          }
          const halo=c.tagName==='text' && getComputedStyle(c).paintOrder==='stroke';
          if(c.tagName==='text'){ if(!halo) txt.push({t:(c.textContent||'').slice(0,10),b:k}); } else vis.push(k);
        }
        for(const {t:label,b} of txt) for(const v of vis){
          const ox=Math.min(b.r,v.r)-Math.max(b.l,v.l), oy=Math.min(b.b,v.b)-Math.max(b.t,v.t);
          if(ox>1&&oy>1) out.push(`压图形：文字「${label}」`);
        }
        for(let i=0;i<txt.length;i++) for(let j=i+1;j<txt.length;j++){
          const a=txt[i].b,c=txt[j].b;
          const ox=Math.min(a.r,c.r)-Math.max(a.l,c.l), oy=Math.min(a.b,c.b)-Math.max(a.t,c.t);
          if(ox>1&&oy>1) out.push(`文字互压：「${txt[i].t}」×「${txt[j].t}」`);
        }
      }
      return [...new Set(out)];
    });
    probs.push(...svgProbs.slice(0,4));
    probs.push(...[...new Set(info.imgHits)].slice(0,4));
    probs.push(...[...new Set(info.textOverflow)].slice(0,4));
    probs.push(...[...new Set(info.boxOverflow)].slice(0,4));
    probs.push(...[...new Set(info.imgOverBorder)].slice(0,4));
    report.push({file,cardWidth:Math.round(box.width),scale:+scale.toFixed(3),minKeyMobile:minKey,minAnyMobile:minAny,smallest,problems:probs,widest:info.widest});
    if(probs.length) failed++;
  }

  // 图 2 专项（仅当该图是柱状图时）：柱子的方向/高度必须和标签一致（+ 在上、− 在下，|值| 越大越高）
  if(await page.locator('#fig-02 svg rect').count()){
  const bars=await page.locator('#fig-02 svg rect').evaluateAll(rs=>rs.map(r=>({y:+r.getAttribute('y'),h:+r.getAttribute('height')})));
  const axis=105, unit=15;            // 轴在 y=105；每 1 个百分点 = 15px
  const badBars=bars.filter(b=>{
    const up=b.y+b.h===axis, down=b.y===axis;
    if(!up&&!down) return true;
    const value=(up?1:-1)*(b.h/unit);
    return ![1,-1,2,-2].includes(Math.round(value));
  });
  if(badBars.length){ failed++; report.push({file:'02-三组偏离.png',problems:[`有 ${badBars.length} 根柱子方向和数值对不上`]}); }

  // 图 2 专项：标签文字不得压到柱子上
  const overlap=await page.locator('#fig-02 svg').first().evaluate(svg=>{
    const rects=[...svg.querySelectorAll('rect')].map(r=>r.getBoundingClientRect());
    const texts=[...svg.querySelectorAll('text')].map(t=>({t:t.textContent,b:t.getBoundingClientRect()}));
    const hit=[];
    for(const {t,b} of texts) for(const r of rects){
      const ox=Math.min(b.right,r.right)-Math.max(b.left,r.left);
      const oy=Math.min(b.bottom,r.bottom)-Math.max(b.top,r.top);
      if(ox>1&&oy>1) hit.push(t);
    }
    return hit;
  });
  if(overlap.length){ failed++; report.push({file:'02-三组偏离.png',problems:[`有 ${overlap.length} 个标签压住柱子：${overlap.slice(0,4).join(',')}`]}); }
  }

  await browser.close();
  console.log(JSON.stringify(report,null,2));
  if(failed){ console.error(`FAILED: ${failed} 张卡片没过图片自检`); process.exit(1); }
})().catch(e=>{console.error('ERROR:',e.message);process.exit(1)});
