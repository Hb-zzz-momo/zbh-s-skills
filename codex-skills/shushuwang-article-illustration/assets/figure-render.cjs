// 模板：把 figures.html 里的卡片渲染成 PNG，并断言每张卡必须有指定文字。放到文章目录的 编辑记录/ 下使用（脚本按 __dirname/.. 找文章根目录）。
const {chromium}=require('C:/Users/zbh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
const path=require('path');
const {pathToFileURL}=require('url');

const root=path.resolve(__dirname,'..');
const outDir=path.join(root,'配图');
fs.mkdirSync(outDir,{recursive:true});

const targets=[
  ['fig-cover','00-封面.png'],
  ['fig-01','01-两资产机制.png'],
  ['fig-02','02-三组偏离.png'],
  ['fig-03','03-公式卡.png'],
  ['fig-04','04-相关系数刻度.png'],
  ['fig-05','05-自测卡.png'],
];

// 交付前必须逐字出现在图里的中文/数字，缺一个就说明排版或字体出了问题
const mustContain={
  'fig-cover':['基金投资第 2 课','两个资产会不会一起动','协方差 · 相关系数','炒技鼠鼠王'],
  'fig-01':['第 1 课：单资产','第 2 课：两个资产','第 3 课：装进同一个组合','同向还是反向','相关系数在这里开始起作用'],
  'fig-02':['A 的偏离不变','同向','反向','交错','协方差 = +2','协方差 = −2','协方差 = 0','+2','−2','+1','−1'],
  'fig-03':['公式 1｜协方差','公式 2｜相关系数','Cov(A,B)','ρ','σ','÷','−1 到 +1'],
  'fig-04':['完全反向','没有线性联动','完全同向','越靠近 −1，越对冲','越靠近 +1，越同步','−1','0','+1'],
  'fig-05':['自测 3 题','7%、3%、7%、3%','协方差 +2','标准差 2%','−1 和 0'],
};

(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const page=await browser.newPage({viewport:{width:2400,height:1200},deviceScaleFactor:2});
  await page.goto(pathToFileURL(path.join(__dirname,'figures.html')).href);
  await page.evaluate(()=>document.fonts.ready);
  await page.locator('img').evaluateAll(xs=>Promise.all(xs.map(i=>i.decode())));

  const broken=await page.locator('img').evaluateAll(xs=>xs.filter(i=>!(i.complete&&i.naturalWidth>0)).length);
  if(broken) throw Error('logo 未加载：'+broken);

  const report=[];
  for(const [id,file] of targets){
    const el=page.locator('#'+id);
    const text=(await el.innerText()).replace(/\s+/g,' ');
    for(const s of mustContain[id]){
      if(!text.includes(s.replace(/\s+/g,' '))) throw Error(`${id} 缺少文字：${s}`);
    }
    const box=await el.boundingBox();
    const dest=path.join(outDir,file);
    await el.screenshot({path:dest});
    const size=fs.statSync(dest).size;
    if(size<20000) throw Error(`${file} 文件过小，可能空白：${size}`);
    report.push({id,file,w:Math.round(box.width),h:Math.round(box.height),bytes:size});
  }
  await browser.close();
  console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error('FAILED:',e.message);process.exit(1)});
