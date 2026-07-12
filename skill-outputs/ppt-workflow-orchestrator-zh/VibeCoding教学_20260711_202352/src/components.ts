import { T } from "./theme.ts";

export type GeometryItem = {
  slide_id: string;
  component: string;
  x: number;
  y: number;
  w: number;
  h: number;
  purpose: string;
  kind?: "line" | "shape" | "text";
};

export function register(manifest: GeometryItem[], slideId: string, component: string, box: any, purpose: string, kind: "line" | "shape" | "text" = "shape") {
  manifest.push({ slide_id: slideId, component, x: box.x, y: box.y, w: box.w, h: box.h, purpose, kind });
}

export function addRect(slide: any, manifest: GeometryItem[], slideId: string, box: any, fill: string, line = fill, purpose = "矩形", options: any = {}) {
  slide.addShape(options.shape || "rect", {
    ...box,
    fill: { color: fill, transparency: options.transparency ?? 0 },
    line: { color: line, width: options.lineWidth ?? 0.8, transparency: options.lineTransparency ?? 0 },
    rotate: options.rotate ?? 0,
    shadow: options.shadow,
    radius: 0,
    objectName: options.objectName
  });
  register(manifest, slideId, options.component || "rect", box, purpose, "shape");
}

export function addLine(slide: any, manifest: GeometryItem[], slideId: string, box: any, color: string, purpose = "线条", options: any = {}) {
  slide.addShape("line", {
    ...box,
    line: { color, width: options.width ?? 1, dash: options.dash, beginArrowType: options.beginArrowType, endArrowType: options.endArrowType }
  });
  register(manifest, slideId, options.component || "line", box, purpose, "line");
}

export function addText(slide: any, manifest: GeometryItem[], slideId: string, text: string, box: any, purpose = "文本", options: any = {}) {
  slide.addText(text, {
    ...box,
    fontFace: options.fontFace || T.fonts.body,
    fontSize: options.fontSize ?? T.sizes.body,
    bold: options.bold ?? false,
    color: options.color || T.colors.ink,
    align: options.align || "left",
    valign: options.valign || "top",
    margin: options.margin ?? 0,
    fit: options.fit || "shrink",
    breakLine: false,
    charSpacing: options.charSpacing,
    rotate: options.rotate ?? 0,
    isTextBox: true,
    fill: options.fill ? { color: options.fill, transparency: options.fillTransparency ?? 0 } : undefined,
    line: options.line ? { color: options.line, width: options.lineWidth ?? 1 } : undefined,
    objectName: options.objectName
  });
  register(manifest, slideId, options.component || "text", box, purpose, "text");
}

export function addArrow(slide: any, manifest: GeometryItem[], slideId: string, x: number, y: number, w: number, color: string, component = "process-arrow") {
  addLine(slide, manifest, slideId, { x, y, w, h: 0 }, color, "阅读方向", { width: 1.1, endArrowType: "triangle", component });
}

export function addMicroHeader(slide: any, manifest: GeometryItem[], slideId: string, page: string, section: string, dark: boolean) {
  const c = dark ? T.colors.white : T.colors.ink;
  addText(slide, manifest, slideId, page, { x: 10.82, y: 0.22, w: 0.44, h: 0.16 }, "页码", { fontFace: T.fonts.latin, fontSize: 7.5, bold: true, color: c, component: "micro-page" });
  addText(slide, manifest, slideId, section, { x: 11.30, y: 0.22, w: 1.50, h: 0.16 }, "章节", { fontFace: T.fonts.latin, fontSize: 7.5, color: c, align: "right", component: "micro-section" });
}

export function addFooter(slide: any, manifest: GeometryItem[], slideId: string, refs: string[], dark: boolean) {
  const c = dark ? "EAF0F7" : T.colors.muted;
  addLine(slide, manifest, slideId, { x: 0.38, y: 7.14, w: 12.55, h: 0 }, dark ? "363636" : T.colors.soft, "页脚线", { width: 0.6, component: "footer-rule" });
  addText(slide, manifest, slideId, `来源：${refs.join(" · ")}`, { x: 0.38, y: 7.20, w: 8.8, h: 0.13 }, "来源脚注", { fontSize: 7.5, color: c, component: "source-footer" });
}

export function addStamp(slide: any, manifest: GeometryItem[], slideId: string, text: string, box: any, dark = false) {
  const c = dark ? T.colors.white : T.colors.blue;
  addText(slide, manifest, slideId, text, box, "校样章", { fontSize: 9, bold: true, color: c, align: "center", valign: "mid", line: c, lineWidth: 1.1, rotate: -2, component: "proof-stamp" });
}

export function addCodePanel(slide: any, manifest: GeometryItem[], slideId: string, box: any, label: string, lines: string[], inverse = false) {
  const bg = inverse ? T.colors.paper : T.colors.black;
  const fg = inverse ? T.colors.ink : T.colors.white;
  const dim = inverse ? T.colors.muted : "9EA5AA";
  addRect(slide, manifest, slideId, box, bg, inverse ? T.colors.soft : T.colors.black, `${label} 代码界面`, { lineWidth: inverse ? 0.7 : 0, component: "code-panel" });
  addText(slide, manifest, slideId, label, { x: box.x + 0.18, y: box.y + 0.16, w: box.w - 0.36, h: 0.20 }, "界面标签", { fontFace: T.fonts.latin, fontSize: 8, bold: true, color: inverse ? T.colors.blueDark : "BFD4FF", charSpacing: 1.1, component: "code-label" });
  lines.slice(0, 7).forEach((line, i) => {
    addText(slide, manifest, slideId, line, { x: box.x + 0.18, y: box.y + 0.52 + i * 0.30, w: box.w - 0.36, h: 0.20 }, "代码行", { fontFace: T.fonts.mono, fontSize: 8.5, color: i % 3 === 0 ? fg : dim, component: "code-line" });
  });
}
