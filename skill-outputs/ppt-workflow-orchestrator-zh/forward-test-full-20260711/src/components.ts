import { THEME as T } from "./theme.ts";

export type GeometryItem = {
  slide_id: string;
  component: string;
  x: number;
  y: number;
  w: number;
  h: number;
  purpose: string;
};

export function register(manifest: GeometryItem[], slideId: string, component: string, box: any, purpose: string) {
  manifest.push({ slide_id: slideId, component, x: box.x, y: box.y, w: box.w, h: box.h, purpose });
}

export function addRect(slide: any, manifest: GeometryItem[], slideId: string, box: any, fill: string, line: string, purpose: string, options: any = {}) {
  slide.addShape("rect", { ...box, fill: { color: fill, transparency: options.fillTransparency ?? 0 }, line: { color: line, width: options.lineWidth ?? 0.8, transparency: options.lineTransparency ?? 0 }, rotate: options.rotate ?? 0, shadow: options.shadow });
  register(manifest, slideId, options.component || "rect", box, purpose);
}

export function addLine(slide: any, manifest: GeometryItem[], slideId: string, box: any, color: string, purpose: string, options: any = {}) {
  slide.addShape("line", { ...box, line: { color, width: options.width ?? 1.0, dash: options.dash, beginArrowType: options.beginArrowType, endArrowType: options.endArrowType } });
  register(manifest, slideId, options.component || "line", box, purpose);
}

export function addText(slide: any, manifest: GeometryItem[], slideId: string, text: string, box: any, purpose: string, options: any = {}) {
  slide.addText(text, {
    ...box,
    fontFace: options.fontFace || T.fonts.body,
    fontSize: options.fontSize || T.sizes.body,
    bold: options.bold ?? false,
    color: options.color || T.colors.ink,
    align: options.align || "left",
    valign: options.valign || "top",
    margin: options.margin ?? 0,
    breakLine: false,
    fit: options.fit || "shrink",
    rotate: options.rotate ?? 0,
    charSpacing: options.charSpacing,
    isTextBox: true,
    fill: options.fillColor ? { color: options.fillColor, transparency: options.fillTransparency ?? 0 } : undefined,
    objectName: options.objectName
  });
  register(manifest, slideId, options.component || "text", box, purpose);
}

export function addTitle(slide: any, manifest: GeometryItem[], slideId: string, pageNo: string, eyebrow: string, title: string, dark = false) {
  const track = { x: 0.62, y: 0.53, w: 0.08, h: 0.36 };
  addRect(slide, manifest, slideId, track, dark ? T.colors.vermilion : T.colors.forest, dark ? T.colors.vermilion : T.colors.forest, "页码轨道", { lineWidth: 0, component: "page-track" });
  addText(slide, manifest, slideId, pageNo, { x: 0.80, y: 0.50, w: 0.58, h: 0.24 }, "页码", { fontSize: T.sizes.label, bold: true, color: dark ? T.colors.white : T.colors.forest, valign: "mid", component: "page-number" });
  addText(slide, manifest, slideId, eyebrow, { x: 1.42, y: 0.50, w: 4.8, h: 0.24 }, "页面分类", { fontSize: T.sizes.label, bold: true, color: dark ? "F5B5A5" : T.colors.vermilion, valign: "mid", charSpacing: 1.2, component: "eyebrow" });
  addText(slide, manifest, slideId, title, { x: 0.62, y: 0.96, w: 12.05, h: 0.62 }, "结论标题", { fontFace: T.fonts.head, fontSize: T.sizes.title, bold: true, color: dark ? T.colors.white : T.colors.forest, component: "title" });
}

export function addFooter(slide: any, manifest: GeometryItem[], slideId: string, source: string, dark = false) {
  addLine(slide, manifest, slideId, { x: 0.62, y: 7.02, w: 12.09, h: 0 }, dark ? "557268" : T.colors.line, "页脚分隔", { width: 0.7, component: "footer-rule" });
  addText(slide, manifest, slideId, source, { x: 0.62, y: 7.08, w: 10.9, h: 0.16 }, "来源", { fontSize: 9, color: dark ? "C9D4CF" : T.colors.muted, valign: "mid", component: "source-footer" });
}

export function addStamp(slide: any, manifest: GeometryItem[], slideId: string, text: string, box: any, purpose: string, dark = false) {
  const stampColor = dark ? "F5B5A5" : T.colors.vermilion;
  slide.addText(text, { ...box, fontFace: T.fonts.body, fontSize: T.sizes.label, bold: true, color: stampColor, align: "center", valign: "mid", margin: 0.05, fit: "shrink", line: { color: stampColor, width: 1.7 }, rotate: -2, isTextBox: true });
  register(manifest, slideId, "stamp", box, purpose);
}

export function addArrow(slide: any, manifest: GeometryItem[], slideId: string, x: number, y: number, w: number, color = T.colors.forest2) {
  addLine(slide, manifest, slideId, { x, y, w, h: 0 }, color, "流程方向", { width: 1.4, endArrowType: "triangle", component: "process-arrow" });
}
