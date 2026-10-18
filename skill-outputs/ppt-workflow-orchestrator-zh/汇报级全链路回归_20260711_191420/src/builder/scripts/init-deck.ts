import fs from "node:fs";
import path from "node:path";
import pptxgenModule from "pptxgenjs";
import { mergeTheme } from "./theme.ts";
import { addBody, addMetric, addSourceFooter, addTitle, register, type GeometryItem } from "./components.ts";
import { parsePresentationDesign } from "./design.ts";

function usage() { console.log("Usage: tsx init-deck.ts --spec slide-spec.json --design PRESENTATION_DESIGN.md --output presentation.pptx [--slides S01,S04,S08] [--assets-root assets] [--chart-spec chart.json] [--manifest build-manifest.json]"); }
function argsOf(argv: string[]) {
  const out: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (key === "--help" || key === "-h") out.help = true;
    else if (key.startsWith("--")) { const value = argv[i + 1]; if (!value || value.startsWith("--")) throw new Error(`Missing value for ${key}`); out[key.slice(2)] = value; i++; }
  }
  return out;
}
function readJson(file: string) { try { return JSON.parse(fs.readFileSync(file, "utf8")); } catch (error: any) { throw new Error(`Cannot read JSON ${file}: ${error.message}`); } }
function blockText(slideSpec: any) { return (slideSpec.content_blocks || []).map((b: any) => b.content ?? b.label ?? b.value ?? "").filter(Boolean).join("\n"); }
function assetPath(root: string, value: string) { const base=path.resolve(root); const out=path.resolve(base,value); const rel=path.relative(base,out); if (rel.startsWith("..")||path.isAbsolute(rel)) throw new Error(`Asset escapes --assets-root: ${value}`); if (!fs.existsSync(out)) throw new Error(`Asset not found: ${out}`); return out; }
function svgData(file: string) { return `data:image/svg+xml;base64,${fs.readFileSync(file).toString("base64")}`; }

type RenderContext = { assetsRoot: string; chartSpec?: any; objectCounts: Record<string,number> };
function count(ctx: RenderContext, type: string) { ctx.objectCounts[type]=(ctx.objectCounts[type]||0)+1; }
function renderNativeVisual(slide:any, slideSpec:any, theme:any, manifest:GeometryItem[], ctx:RenderContext) {
  const id=slideSpec.slide_id; const blocks=slideSpec.content_blocks||[]; const chartBlock=blocks.find((b:any)=>b.type==="chart"); const tableBlock=blocks.find((b:any)=>b.type==="table"); const imageBlock=blocks.find((b:any)=>b.type==="image"); const svgBlock=blocks.find((b:any)=>b.type==="svg");
  if (!chartBlock && !tableBlock && !imageBlock && !svgBlock) return false;
  addTitle(slide,manifest,id,slideSpec.claim||slideSpec.purpose,theme);
  if (chartBlock) {
    const chart=chartBlock.spec ? readJson(assetPath(ctx.assetsRoot,chartBlock.spec)) : ctx.chartSpec; if (!chart) throw new Error(`${id} chart block has no chart spec`);
    const data=(chart.series||[]).map((s:any)=>({name:s.name,labels:chart.categories,values:s.values})); const type=chart.chart_type==="line"?"line":chart.chart_type==="pie"?"pie":"bar";
    slide.addChart(type,data,{x:0.82,y:1.55,w:8.45,h:4.9,showLegend:data.length>1,legendPos:"b",showTitle:false,showValue:true,showCatName:false,showSerName:false,showPercent:false,showLeaderLines:false,showValAxisTitle:true,valAxisTitle:chart.unit?`单位：${chart.unit}`:"数值",showCatAxisTitle:false,catAxisLabelFontFace:theme.fonts.body,catAxisLabelFontSize:10,valAxisLabelFontFace:theme.fonts.body,valAxisLabelFontSize:10,chartColors:[theme.colors.accent,theme.colors.accent2,"F1B24A","6C7A89"],barDir:chart.chart_type==="bar"?"bar":"col",catAxisLabelRotate:0,valAxisMinVal:chart.axis?.zero_baseline?0:undefined});
    const box={x:0.82,y:1.55,w:8.45,h:4.9}; register(manifest,id,"native-chart",box,chart.title||"图表"); count(ctx,"charts");
    addBody(slide,manifest,id,slideSpec.audience_takeaway||"",theme,{x:9.65,y:2.0,w:2.8,h:2.6},{fontSize:18,bold:true,color:theme.colors.accent2});
  } else if (tableBlock) {
    const rows=tableBlock.rows; if (!Array.isArray(rows)||!rows.length) throw new Error(`${id} table rows missing`);
    slide.addTable(rows,{x:0.85,y:1.65,w:11.65,h:4.7,border:{type:"solid",color:theme.colors.line,pt:1},fill:theme.colors.surface,color:theme.colors.ink,fontFace:theme.fonts.body,fontSize:14,margin:0.08,bold:false,rowH:0.55,colW:tableBlock.col_widths,autoFit:false});
    register(manifest,id,"native-table",{x:0.85,y:1.65,w:11.65,h:4.7},"原生表格"); count(ctx,"tables");
  } else {
    const block=imageBlock||svgBlock; const file=assetPath(ctx.assetsRoot,block.path); const box={x:0.8,y:1.45,w:8.0,h:5.25};
    slide.addImage(svgBlock?{data:svgData(file),...box,altText:block.alt||"SVG visual",objectName:`${id}-svg`}:{path:file,...box,sizing:{type:block.fit||"cover",w:box.w,h:box.h},altText:block.alt||"Visual",objectName:`${id}-image`});
    register(manifest,id,svgBlock?"svg":"image",box,block.alt||""); count(ctx,svgBlock?"svg":"images");
    addBody(slide,manifest,id,slideSpec.audience_takeaway||"",theme,{x:9.35,y:2.0,w:3.05,h:2.8},{fontSize:18,bold:true,color:theme.colors.accent2});
  }
  addSourceFooter(slide,manifest,id,slideSpec.source_footer||[],theme); if (slideSpec.speaker_notes) slide.addNotes(slideSpec.speaker_notes); return true;
}

function renderSlide(pptx: any, slideSpec: any, theme: any, manifest: GeometryItem[], ctx:RenderContext) {
  const slide = pptx.addSlide({masterName:"REPORT_MASTER"}); const id = slideSpec.slide_id; slide.background = { color: theme.colors.paper };
  if (renderNativeVisual(slide,slideSpec,theme,manifest,ctx)) return;
  if (slideSpec.layout_family === "hero") {
    const bar = { x: 0.0, y: 0.0, w: 0.22, h: 7.5 };
    slide.addShape("rect", { ...bar, fill: { color: theme.colors.accent }, line: { color: theme.colors.accent } }); register(manifest, id, "motif-bar", bar, "视觉母题");
    const titleBox = { x: 0.85, y: 1.45, w: 8.7, h: 1.5 };
    slide.addText(slideSpec.claim || slideSpec.purpose, { ...titleBox, fontFace: theme.fonts.head, fontSize: theme.sizes.hero, bold: true, color: theme.colors.ink, margin: 0, fit: "shrink" }); register(manifest, id, "hero-title", titleBox, "核心主张");
    addBody(slide, manifest, id, slideSpec.audience_takeaway || "", theme, { x: 0.9, y: 3.35, w: 7.5, h: 1.0 }, { fontSize: 18, color: theme.colors.muted });
    addMetric(slide, manifest, id, id, slideSpec.section || "", theme, { x: 10.0, y: 1.55, w: 2.35, h: 1.55 });
  } else if (slideSpec.layout_family === "process" || slideSpec.visual_type?.includes("process")) {
    addTitle(slide, manifest, id, slideSpec.claim || slideSpec.purpose, theme);
    const items = (slideSpec.content_blocks || []).slice(0, 5); const n = Math.max(items.length, 1); const gap = 0.42; const w = (11.8 - gap * (n - 1)) / n;
    items.forEach((item: any, index: number) => { const box = { x: 0.75 + index * (w + gap), y: 2.45, w, h: 1.55 }; slide.addShape("roundRect", { ...box, fill: { color: index % 2 ? theme.colors.surface : "E8F3F1" }, line: { color: theme.colors.accent2, width: 1.2 }, radius: theme.radius }); slide.addText(item.content || item.label || "", { x: box.x + 0.12, y: box.y + 0.18, w: box.w - 0.24, h: box.h - 0.36, fontFace: theme.fonts.body, fontSize: 15, bold: true, align: "center", valign: "mid", color: theme.colors.ink, margin: 0.02, fit: "shrink" }); register(manifest, id, "process-node", box, item.content || ""); if (index < n - 1) { const arrow = { x: box.x + box.w + 0.05, y: box.y + box.h / 2, w: gap - 0.10, h: 0.001 }; slide.addShape("line", { ...arrow, line: { color: theme.colors.accent2, width: 1.4, endArrowType: "triangle" } }); register(manifest, id, "process-arrow", arrow, "流程方向"); } });
    addBody(slide, manifest, id, slideSpec.audience_takeaway || "", theme, { x: 1.35, y: 5.15, w: 10.6, h: 0.8 }, { align: "center", color: theme.colors.muted });
  } else if (slideSpec.layout_family === "data-focus" || slideSpec.visual_type?.includes("chart")) {
    addTitle(slide, manifest, id, slideSpec.claim || slideSpec.purpose, theme);
    const values = (slideSpec.content_blocks || []).filter((b: any) => b.type === "metric");
    (values.length ? values : [{ value: "—", label: "待提供真实数据" }]).slice(0, 3).forEach((item: any, i: number) => addMetric(slide, manifest, id, String(item.value ?? item.content ?? "—"), item.label || "指标", theme, { x: 0.9 + i * 4.15, y: 2.0, w: 3.55, h: 1.7 }));
    addBody(slide, manifest, id, slideSpec.audience_takeaway || blockText(slideSpec), theme, { x: 1.0, y: 4.45, w: 11.2, h: 1.15 }, { align: "center" });
  } else if (slideSpec.layout_family === "split") {
    addTitle(slide, manifest, id, slideSpec.claim || slideSpec.purpose, theme);
    const items = (slideSpec.content_blocks || []).slice(0, 2);
    items.forEach((item: any, index: number) => { const box = { x: 0.85 + index * 6.0, y: 2.0, w: 5.55, h: 2.55 }; slide.addShape("roundRect", { ...box, fill: { color: index ? "E8F3F1" : theme.colors.surface }, line: { color: index ? theme.colors.accent2 : theme.colors.line, width: 1.2 } }); slide.addText(item.content || item.label || "", { x: box.x + 0.35, y: box.y + 0.35, w: box.w - 0.7, h: box.h - 0.7, fontFace: theme.fonts.body, fontSize: 18, bold: true, color: theme.colors.ink, margin: 0, valign: "mid", fit: "shrink" }); register(manifest, id, "split-panel", box, item.content || ""); });
    const takeaway = { x: 1.65, y: 5.35, w: 10.0, h: 0.75 }; slide.addShape("roundRect", { ...takeaway, fill: { color: theme.colors.accent2, transparency: 88 }, line: { color: theme.colors.accent2, transparency: 100 } }); slide.addText(slideSpec.audience_takeaway || "", { ...takeaway, fontFace: theme.fonts.head, fontSize: 16, bold: true, align: "center", valign: "mid", color: theme.colors.accent2, margin: 0.05, fit: "shrink" }); register(manifest, id, "takeaway-band", takeaway, "听众记忆点");
  } else if (slideSpec.layout_family === "comparison") {
    addTitle(slide, manifest, id, slideSpec.claim || slideSpec.purpose, theme);
    const items = (slideSpec.content_blocks || []).slice(0, 4);
    items.forEach((item: any, index: number) => { const col=index%2, row=Math.floor(index/2); const box={x:0.9+col*6.05,y:1.75+row*2.25,w:5.55,h:1.75}; slide.addShape("roundRect",{...box,fill:{color:index===0?"FDEDE9":index===3?"E8F3F1":theme.colors.surface},line:{color:index===0?theme.colors.accent:theme.colors.accent2,width:1.1}}); slide.addText(item.content||item.label||"",{x:box.x+0.3,y:box.y+0.25,w:box.w-0.6,h:box.h-0.5,fontFace:theme.fonts.body,fontSize:17,bold:true,color:theme.colors.ink,margin:0,valign:"mid",fit:"shrink"}); register(manifest,id,"comparison-cell",box,item.content||""); });
  } else {
    addTitle(slide, manifest, id, slideSpec.claim || slideSpec.purpose, theme); addBody(slide, manifest, id, blockText(slideSpec) || slideSpec.audience_takeaway || "", theme, { x: 0.9, y: 1.65, w: 7.4, h: 4.7 });
    const panel = { x: 9.1, y: 1.65, w: 3.25, h: 4.7 }; slide.addShape("roundRect", { ...panel, fill: { color: "E8F3F1" }, line: { color: theme.colors.accent2, width: 1.2 } }); slide.addText(slideSpec.audience_takeaway || slideSpec.section || "", { x: panel.x + 0.25, y: panel.y + 0.35, w: panel.w - 0.5, h: panel.h - 0.7, fontFace: theme.fonts.head, fontSize: 20, bold: true, color: theme.colors.accent2, margin: 0, valign: "mid", fit: "shrink" }); register(manifest, id, "takeaway-panel", panel, "听众记忆点");
  }
  addSourceFooter(slide, manifest, id, slideSpec.source_footer || [], theme); if (slideSpec.speaker_notes) slide.addNotes(slideSpec.speaker_notes);
}

async function main() {
  const args = argsOf(process.argv.slice(2)); if (args.help) { usage(); return; } if (!args.spec || !args.output || !args.design) { usage(); throw new Error("--spec, --design and --output are required"); }
  const specPath = path.resolve(String(args.spec)); const outputPath = path.resolve(String(args.output)); const spec = readJson(specPath);
  if (!Array.isArray(spec.slides) || spec.slides.length === 0) throw new Error("spec.slides must be a non-empty array");
  const ids = spec.slides.map((s: any) => s.slide_id); if (new Set(ids).size !== ids.length || ids.some((id: any) => !id)) throw new Error("Every slide_id must be non-empty and unique");
  const parsedDesign=parsePresentationDesign(path.resolve(String(args.design))); const theme = args.theme ? mergeTheme({...parsedDesign.theme,...readJson(path.resolve(String(args.theme)))}) : parsedDesign.theme; fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  const PptxGenJS: any = typeof pptxgenModule === "function" ? pptxgenModule : (pptxgenModule as any).default;
  if (typeof PptxGenJS !== "function") throw new Error("pptxgenjs did not expose a constructor through ESM or CJS default export");
  const pptx = new PptxGenJS(); pptx.layout = "LAYOUT_WIDE"; pptx.author = spec.deck?.author || "Codex"; pptx.company = spec.deck?.company || ""; pptx.subject = spec.deck?.presentation_type || "Presentation"; pptx.title = spec.deck?.title || "Presentation"; pptx.lang = spec.deck?.language || "zh-CN"; pptx.theme = { headFontFace: theme.fonts.head, bodyFontFace: theme.fonts.body, lang: pptx.lang };
  pptx.defineSlideMaster({title:"REPORT_MASTER",background:{color:theme.colors.paper},objects:[{line:{x:0.65,y:7.02,w:12.0,h:0,line:{color:theme.colors.line,width:0.8}}}],slideNumber:{x:12.35,y:7.08,w:0.35,h:0.18,fontFace:theme.fonts.body,fontSize:9,color:theme.colors.muted,align:"right",margin:0}});
  const selected=args.slides?new Set(String(args.slides).split(",").map(s=>s.trim()).filter(Boolean)):null; const slides=selected?spec.slides.filter((s:any)=>selected.has(s.slide_id)):spec.slides; if(selected&&slides.length!==selected.size) throw new Error(`Unknown slide id in --slides; selected ${selected.size}, found ${slides.length}`);
  const ctx:RenderContext={assetsRoot:path.resolve(String(args["assets-root"]||path.dirname(specPath))),chartSpec:args["chart-spec"]?readJson(path.resolve(String(args["chart-spec"]))):undefined,objectCounts:{}};
  const manifest: GeometryItem[] = []; slides.forEach((slide: any) => renderSlide(pptx, slide, theme, manifest,ctx)); await pptx.writeFile({ fileName: outputPath, compression:true });
  const manifestPath = path.resolve(String(args.manifest || `${outputPath}.manifest.json`)); fs.mkdirSync(path.dirname(manifestPath), { recursive: true }); fs.writeFileSync(manifestPath, JSON.stringify({ slide_size: theme.slide, source_spec: specPath, design:path.resolve(String(args.design)), output: outputPath, slide_ids:slides.map((s:any)=>s.slide_id), object_counts:ctx.objectCounts, elements: manifest }, null, 2), "utf8"); console.log(JSON.stringify({ output: outputPath, manifest: manifestPath, slides: slides.length,object_counts:ctx.objectCounts }));
}
main().catch((error) => { console.error(`ERROR: ${error.stack || error.message}`); process.exitCode = 1; });
