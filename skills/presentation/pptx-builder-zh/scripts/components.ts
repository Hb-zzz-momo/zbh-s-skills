export type GeometryItem = { slide_id: string; component: string; x: number; y: number; w: number; h: number; purpose?: string };

export function register(manifest: GeometryItem[], slideId: string, component: string, box: any, purpose = "") {
  manifest.push({ slide_id: slideId, component, x: box.x, y: box.y, w: box.w, h: box.h, purpose });
}

export function addTitle(slide: any, manifest: GeometryItem[], slideId: string, text: string, theme: any, box = { x: 0.65, y: 0.45, w: 12.0, h: 0.75 }) {
  slide.addText(text, { ...box, fontFace: theme.fonts.head, fontSize: theme.sizes.title, bold: true, color: theme.colors.ink, margin: 0, fit: "shrink" });
  register(manifest, slideId, "title", box, "结论标题");
}

export function addSourceFooter(slide: any, manifest: GeometryItem[], slideId: string, refs: string[], theme: any) {
  if (!refs || refs.length === 0) return;
  const box = { x: 0.65, y: 7.08, w: 12.0, h: 0.18 };
  slide.addText(`来源：${refs.join(" · ")}`, { ...box, fontFace: theme.fonts.body, fontSize: theme.sizes.small, color: theme.colors.muted, margin: 0, fit: "shrink" });
  register(manifest, slideId, "source-footer", box, "来源脚注");
}

export function addMetric(slide: any, manifest: GeometryItem[], slideId: string, value: string, label: string, theme: any, box: any) {
  slide.addShape("roundRect", { ...box, rectRadius: theme.radius, fill: { color: theme.colors.surface }, line: { color: theme.colors.line, width: 1 } });
  slide.addText(value, { x: box.x + 0.2, y: box.y + 0.18, w: box.w - 0.4, h: 0.55, fontFace: theme.fonts.head, fontSize: theme.sizes.metric, bold: true, color: theme.colors.accent, margin: 0, fit: "shrink" });
  slide.addText(label, { x: box.x + 0.2, y: box.y + 0.85, w: box.w - 0.4, h: 0.4, fontFace: theme.fonts.body, fontSize: theme.sizes.body, color: theme.colors.ink, margin: 0, fit: "shrink" });
  register(manifest, slideId, "metric", box, label);
}

export function addBody(slide: any, manifest: GeometryItem[], slideId: string, text: string, theme: any, box: any, options: any = {}) {
  slide.addText(text, { ...box, fontFace: theme.fonts.body, fontSize: theme.sizes.body, color: theme.colors.ink, margin: 0.05, valign: "mid", fit: "shrink", ...options });
  register(manifest, slideId, "body", box, "正文");
}

