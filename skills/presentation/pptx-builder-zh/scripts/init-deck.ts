import fs from "node:fs";
import path from "node:path";
import pptxgen from "pptxgenjs";
import { DEFAULT_THEME, mergeTheme } from "./theme.ts";
import { addBody, addMetric, addSourceFooter, addTitle, register, type GeometryItem } from "./components.ts";

function usage() { console.log("Usage: tsx init-deck.ts --spec slide-spec.json --output presentation.pptx [--theme theme.json] [--manifest build-manifest.json]"); }
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

function renderSlide(pptx: any, slideSpec: any, theme: any, manifest: GeometryItem[]) {
  const slide = pptx.addSlide(); const id = slideSpec.slide_id; slide.background = { color: theme.colors.paper };
  if (slideSpec.layout_family === "hero") {
    const bar = { x: 0.0, y: 0.0, w: 0.22, h: 7.5 };
    slide.addShape("rect", { ...bar, fill: { color: theme.colors.accent }, line: { color: theme.colors.accent } }); register(manifest, id, "motif-bar", bar, "视觉母题");
    const titleBox = { x: 0.85, y: 1.45, w: 8.7, h: 1.5 };
    slide.addText(slideSpec.claim || slideSpec.purpose, { ...titleBox, fontFace: theme.fonts.head, fontSize: theme.sizes.hero, bold: true, color: theme.colors.ink, margin: 0, fit: "shrink" }); register(manifest, id, "hero-title", titleBox, "核心主张");
    addBody(slide, manifest, id, slideSpec.audience_takeaway || "", theme, { x: 0.9, y: 3.35, w: 7.5, h: 1.0 }, { fontSize: 18, color: theme.colors.muted });
    addMetric(slide, manifest, id, id, slideSpec.section || "", theme, { x: 10.0, y: 1.55, w: 2.35, h: 1.55 });
  } else if (slideSpec.layout_family === "process" || slideSpec.visual_type?.includes("process")) {
    addTitle(slide, manifest, id, slideSpec.claim || slideSpec.purpose, theme);
    const items = (slideSpec.content_blocks || []).slice(0, 5); const n = Math.max(items.length, 1); const gap = 0.22; const w = (11.8 - gap * (n - 1)) / n;
    items.forEach((item: any, index: number) => { const box = { x: 0.75 + index * (w + gap), y: 2.45, w, h: 1.55 }; slide.addShape("roundRect", { ...box, fill: { color: index % 2 ? theme.colors.surface : "E8F3F1" }, line: { color: theme.colors.accent2, width: 1.2 }, radius: theme.radius }); slide.addText(item.content || item.label || "", { x: box.x + 0.12, y: box.y + 0.18, w: box.w - 0.24, h: box.h - 0.36, fontFace: theme.fonts.body, fontSize: 15, bold: true, align: "center", valign: "mid", color: theme.colors.ink, margin: 0.02, fit: "shrink" }); register(manifest, id, "process-node", box, item.content || ""); });
    addBody(slide, manifest, id, slideSpec.audience_takeaway || "", theme, { x: 1.35, y: 5.15, w: 10.6, h: 0.8 }, { align: "center", color: theme.colors.muted });
  } else if (slideSpec.layout_family === "data-focus" || slideSpec.visual_type?.includes("chart")) {
    addTitle(slide, manifest, id, slideSpec.claim || slideSpec.purpose, theme);
    const values = (slideSpec.content_blocks || []).filter((b: any) => b.type === "metric");
    (values.length ? values : [{ value: "—", label: "待提供真实数据" }]).slice(0, 3).forEach((item: any, i: number) => addMetric(slide, manifest, id, String(item.value ?? item.content ?? "—"), item.label || "指标", theme, { x: 0.9 + i * 4.15, y: 2.0, w: 3.55, h: 1.7 }));
    addBody(slide, manifest, id, slideSpec.audience_takeaway || blockText(slideSpec), theme, { x: 1.0, y: 4.45, w: 11.2, h: 1.15 }, { align: "center" });
  } else {
    addTitle(slide, manifest, id, slideSpec.claim || slideSpec.purpose, theme); addBody(slide, manifest, id, blockText(slideSpec) || slideSpec.audience_takeaway || "", theme, { x: 0.9, y: 1.65, w: 7.4, h: 4.7 });
    const panel = { x: 9.1, y: 1.65, w: 3.25, h: 4.7 }; slide.addShape("roundRect", { ...panel, fill: { color: "E8F3F1" }, line: { color: theme.colors.accent2, width: 1.2 } }); slide.addText(slideSpec.audience_takeaway || slideSpec.section || "", { x: panel.x + 0.25, y: panel.y + 0.35, w: panel.w - 0.5, h: panel.h - 0.7, fontFace: theme.fonts.head, fontSize: 20, bold: true, color: theme.colors.accent2, margin: 0, valign: "mid", fit: "shrink" }); register(manifest, id, "takeaway-panel", panel, "听众记忆点");
  }
  addSourceFooter(slide, manifest, id, slideSpec.source_footer || [], theme); if (slideSpec.speaker_notes) slide.addNotes(slideSpec.speaker_notes);
}

async function main() {
  const args = argsOf(process.argv.slice(2)); if (args.help) { usage(); return; } if (!args.spec || !args.output) { usage(); throw new Error("--spec and --output are required"); }
  const specPath = path.resolve(String(args.spec)); const outputPath = path.resolve(String(args.output)); const spec = readJson(specPath);
  if (!Array.isArray(spec.slides) || spec.slides.length === 0) throw new Error("spec.slides must be a non-empty array");
  const ids = spec.slides.map((s: any) => s.slide_id); if (new Set(ids).size !== ids.length || ids.some((id: any) => !id)) throw new Error("Every slide_id must be non-empty and unique");
  const theme = args.theme ? mergeTheme(readJson(path.resolve(String(args.theme)))) : DEFAULT_THEME; fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  const pptx = new pptxgen(); pptx.layout = "LAYOUT_WIDE"; pptx.author = spec.deck?.author || "Codex"; pptx.company = spec.deck?.company || ""; pptx.subject = spec.deck?.presentation_type || "Presentation"; pptx.title = spec.deck?.title || "Presentation"; pptx.lang = spec.deck?.language || "zh-CN"; pptx.theme = { headFontFace: theme.fonts.head, bodyFontFace: theme.fonts.body, lang: pptx.lang };
  const manifest: GeometryItem[] = []; spec.slides.forEach((slide: any) => renderSlide(pptx, slide, theme, manifest)); await pptx.writeFile({ fileName: outputPath });
  const manifestPath = path.resolve(String(args.manifest || `${outputPath}.manifest.json`)); fs.writeFileSync(manifestPath, JSON.stringify({ slide_size: theme.slide, source_spec: specPath, output: outputPath, elements: manifest }, null, 2), "utf8"); console.log(JSON.stringify({ output: outputPath, manifest: manifestPath, slides: spec.slides.length }));
}
main().catch((error) => { console.error(`ERROR: ${error.message}`); process.exitCode = 1; });

