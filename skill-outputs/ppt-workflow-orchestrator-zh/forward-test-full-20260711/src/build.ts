import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { THEME as T } from "./theme.ts";
import { addArrow, addFooter, addLine, addRect, addStamp, addText, addTitle, register, type GeometryItem } from "./components.ts";

function loadPptxGenJS() {
  const localRequire = createRequire(import.meta.url);
  try { return localRequire("pptxgenjs"); }
  catch {
    const skillRequire = createRequire("C:/Users/zbh/.agents/skills/presentation/pptx-builder-zh/package.json");
    return skillRequire("pptxgenjs");
  }
}

function parseArgs(argv: string[]) {
  const out: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--help" || argv[i] === "-h") out.help = true;
    else if (argv[i].startsWith("--")) {
      if (!argv[i + 1] || argv[i + 1].startsWith("--")) throw new Error(`Missing value for ${argv[i]}`);
      out[argv[i].slice(2)] = argv[++i];
    }
  }
  return out;
}

function usage() { console.log("tsx build.ts --spec slide-spec.json --output presentation.pptx --manifest build-manifest.json [--slides S01,S03,S04]"); }

function noteFor(spec: any, id: string) { return spec.slides.find((s: any) => s.slide_id === id)?.speaker_notes || ""; }

function setBg(slide: any, color = T.colors.paper) { slide.background = { color }; }

function slide1(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S01"; const s = pptx.addSlide(); setBg(s);
  addText(s, manifest, id, "发布门禁提案 / 6 页技术汇报", { x: 0.70, y: 0.58, w: 4.6, h: 0.28 }, "开场标签", { fontSize: T.sizes.label, bold: true, color: T.colors.vermilion, charSpacing: 1.0, component: "eyebrow" });
  addText(s, manifest, id, "先验证三页，\n再复制方向到整套", { x: 0.70, y: 1.42, w: 6.35, h: 1.72 }, "封面主张", { fontFace: T.fonts.head, fontSize: T.sizes.hero, bold: true, color: T.colors.forest, component: "hero-title" });
  addText(s, manifest, id, "用最小可验证表达面，提前拦截\n叙事、机制与证据风险。", { x: 0.74, y: 3.42, w: 5.7, h: 0.90 }, "副标题", { fontSize: T.sizes.subtitle, color: T.colors.ink, component: "subtitle" });
  addRect(s, manifest, id, { x: 0.72, y: 4.86, w: 5.48, h: 0.62 }, T.colors.forest, T.colors.forest, "行动请求条", { lineWidth: 0, component: "decision-band" });
  addText(s, manifest, id, "请求批准：纳入正式汇报发布门禁", { x: 0.98, y: 5.02, w: 5.0, h: 0.26 }, "行动请求", { fontSize: 16, bold: true, color: T.colors.white, valign: "mid", component: "decision-text" });
  const papers = [
    { x: 7.46, y: 1.20, w: 2.42, h: 4.34, rotate: -6, label: "封面", sub: "主题风险", no: "01" },
    { x: 9.10, y: 1.42, w: 2.42, h: 4.34, rotate: 1, label: "机制", sub: "逻辑风险", no: "02" },
    { x: 10.70, y: 1.67, w: 2.24, h: 4.20, rotate: 7, label: "数据", sub: "可信风险", no: "03" }
  ];
  papers.forEach((p, i) => {
    s.addShape("rect", { x: p.x, y: p.y, w: p.w, h: p.h, fill: { color: i === 1 ? T.colors.paper2 : "F8F2E7" }, line: { color: i === 1 ? T.colors.forest2 : T.colors.line, width: i === 1 ? 1.3 : 0.9 }, rotate: p.rotate, shadow: { type: "outer", color: "827A70", opacity: 0.16, blur: 1.6, angle: 45, distance: 1.1 } });
    register(manifest, id, "paper-sheet", { x: p.x, y: p.y, w: p.w, h: p.h }, `三页母题 ${p.label}`);
    addText(s, manifest, id, p.no, { x: p.x + 0.30, y: p.y + 0.34, w: 0.50, h: 0.30 }, "校样编号", { fontSize: 12, bold: true, color: T.colors.vermilion, rotate: p.rotate, component: "paper-number" });
    addText(s, manifest, id, p.label, { x: p.x + 0.30, y: p.y + 2.35, w: p.w - 0.58, h: 0.48 }, "校样标题", { fontSize: 23, bold: true, color: T.colors.forest, rotate: p.rotate, component: "paper-title" });
    addText(s, manifest, id, p.sub, { x: p.x + 0.32, y: p.y + 2.92, w: p.w - 0.60, h: 0.30 }, "校样风险", { fontSize: 12, color: T.colors.muted, rotate: p.rotate, component: "paper-subtitle" });
  });
  addText(s, manifest, id, "WHY THREE-SLIDE VERTICAL SLICES", { x: 0.72, y: 6.73, w: 5.2, h: 0.18 }, "英文短标", { fontSize: 9, bold: true, color: T.colors.muted, charSpacing: 1.4, component: "micro-label" });
  addFooter(s, manifest, id, "来源：SRC-001 · SRC-002");
  s.addNotes(noteFor(spec, id));
}

function slide2(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S02"; const s = pptx.addSlide(); setBg(s); addTitle(s, manifest, id, "02/06", "WHY THREE", "三页切片覆盖三类关键的方向性错误");
  const cols = [
    { x: 0.74, y: 1.94, w: 3.55, h: 3.64, no: "01", label: "封面", risk: "主题风险", q: "一句话能否让负责人\n知道要批准什么？", signal: "主张与行动", fill: "FBF8F1" },
    { x: 4.55, y: 2.24, w: 3.98, h: 3.92, no: "02", label: "机制", risk: "逻辑风险", q: "最复杂链路\n能否被一次讲清？", signal: "结构与层级", fill: "EEF2EC" },
    { x: 8.80, y: 1.72, w: 3.76, h: 3.46, no: "03", label: "数据", risk: "可信风险", q: "口径、标注与结论\n是否同向？", signal: "证据与边界", fill: "F8ECE7" }
  ];
  cols.forEach((c, i) => {
    addRect(s, manifest, id, { x: c.x, y: c.y, w: c.w, h: c.h }, c.fill, i === 2 ? T.colors.vermilion : T.colors.line, `${c.label}风险探针`, { lineWidth: i === 2 ? 1.2 : 0.8, component: "risk-probe" });
    addText(s, manifest, id, c.no, { x: c.x + 0.28, y: c.y + 0.28, w: 0.48, h: 0.25 }, "探针编号", { fontSize: 11, bold: true, color: T.colors.vermilion, component: "probe-number" });
    addText(s, manifest, id, c.label, { x: c.x + 0.28, y: c.y + 0.72, w: 1.2, h: 0.46 }, "代表页", { fontSize: 25, bold: true, color: T.colors.forest, component: "probe-label" });
    addText(s, manifest, id, c.risk, { x: c.x + c.w - 1.32, y: c.y + 0.78, w: 1.0, h: 0.28 }, "风险类型", { fontSize: 11, bold: true, color: T.colors.vermilion, align: "right", component: "probe-risk" });
    addLine(s, manifest, id, { x: c.x + 0.28, y: c.y + 1.44, w: c.w - 0.56, h: 0 }, T.colors.line, "探针分隔", { width: 0.8, component: "probe-rule" });
    addText(s, manifest, id, c.q, { x: c.x + 0.28, y: c.y + 1.76, w: c.w - 0.56, h: 0.95 }, "验证问题", { fontSize: 17, bold: true, color: T.colors.ink, component: "probe-question" });
    addText(s, manifest, id, `观察信号  /  ${c.signal}`, { x: c.x + 0.28, y: c.y + c.h - 0.54, w: c.w - 0.56, h: 0.22 }, "观察信号", { fontSize: 10.5, color: T.colors.muted, component: "probe-signal" });
  });
  addText(s, manifest, id, "三张通过，才说明这套表达系统值得复制。", { x: 1.20, y: 6.38, w: 10.95, h: 0.38 }, "页面结论", { fontSize: 18, bold: true, color: T.colors.forest, align: "center", valign: "mid", component: "bottom-line" });
  addFooter(s, manifest, id, "来源：SRC-002"); s.addNotes(noteFor(spec, id));
}

function slide3(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S03"; const s = pptx.addSlide(); setBg(s); addTitle(s, manifest, id, "03/06", "GATED LOOP", "切片 PASS，才进入全量构建");
  const steps = [
    ["1", "定契约", "一页一结论"], ["2", "做三页", "封面 / 机制 / 数据"], ["3", "真渲染", "Office → PDF → PNG"], ["4", "查问题", "内容 / 几何 / 视觉"], ["5", "修复复验", "切片与 Montage"]
  ];
  const x0 = 0.72, y = 2.20, w = 1.72, gap = 0.28;
  steps.forEach((st, i) => {
    const x = x0 + i * (w + gap);
    addRect(s, manifest, id, { x, y, w, h: 1.82 }, i === 2 ? "E8EFEA" : T.colors.paper2, i === 2 ? T.colors.forest2 : T.colors.line, `流程 ${st[1]}`, { lineWidth: i === 2 ? 1.3 : 0.8, component: "process-node" });
    addText(s, manifest, id, st[0], { x: x + 0.16, y: y + 0.14, w: 0.30, h: 0.24 }, "步骤编号", { fontSize: 11, bold: true, color: T.colors.vermilion, component: "step-number" });
    addText(s, manifest, id, st[1], { x: x + 0.16, y: y + 0.55, w: w - 0.32, h: 0.36 }, "步骤标题", { fontSize: 18, bold: true, color: T.colors.forest, component: "step-title" });
    addText(s, manifest, id, st[2], { x: x + 0.16, y: y + 1.15, w: w - 0.32, h: 0.34 }, "步骤说明", { fontSize: 10.5, color: T.colors.muted, valign: "mid", component: "step-detail" });
    if (i < steps.length - 1) addArrow(s, manifest, id, x + w + 0.04, y + 0.92, gap - 0.08);
  });
  const gate = { x: 10.82, y: 1.90, w: 1.82, h: 2.42 };
  addRect(s, manifest, id, gate, T.colors.forest, T.colors.forest, "切片 Gate", { lineWidth: 0, component: "gate-panel" });
  addText(s, manifest, id, "SLICE", { x: 11.10, y: 2.22, w: 1.26, h: 0.28 }, "Gate 标签", { fontSize: 11, bold: true, color: "BFD1C9", align: "center", component: "gate-label" });
  addText(s, manifest, id, "PASS", { x: 11.03, y: 2.66, w: 1.38, h: 0.46 }, "Gate 结果", { fontSize: 25, bold: true, color: T.colors.white, align: "center", component: "gate-pass" });
  addText(s, manifest, id, "进入全量\n构建", { x: 11.05, y: 3.40, w: 1.34, h: 0.50 }, "放行动作", { fontSize: 12, bold: true, color: T.colors.white, align: "center", valign: "mid", component: "gate-action" });
  addArrow(s, manifest, id, 10.50, 3.10, 0.24, T.colors.forest);
  addLine(s, manifest, id, { x: 11.74, y: 4.58, w: 0, h: 0.72 }, T.colors.vermilion, "FAIL 回路下行", { width: 1.4, component: "fail-loop" });
  addLine(s, manifest, id, { x: 3.10, y: 5.30, w: 8.64, h: 0 }, T.colors.vermilion, "FAIL 回路返回", { width: 1.4, beginArrowType: "triangle", component: "fail-loop" });
  addText(s, manifest, id, "FAIL：只返工三页", { x: 8.80, y: 5.42, w: 2.85, h: 0.28 }, "失败分支", { fontSize: 11, bold: true, color: T.colors.vermilion, align: "right", component: "fail-label" });
  addText(s, manifest, id, "先缩小错误半径，再扩大生产半径。", { x: 0.88, y: 6.18, w: 7.6, h: 0.38 }, "原则", { fontSize: 18, bold: true, color: T.colors.forest, component: "principle" });
  addStamp(s, manifest, id, "先切片", { x: 10.44, y: 6.06, w: 1.66, h: 0.54 }, "流程校样章");
  addFooter(s, manifest, id, "来源：SRC-002 · SRC-003"); s.addNotes(noteFor(spec, id));
}

function slide4(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S04"; const s = pptx.addSlide(); setBg(s); addTitle(s, manifest, id, "04/06", "ILLUSTRATIVE DATA", "方向错误越晚发现，返工面越大");
  addStamp(s, manifest, id, "示例数据", { x: 10.88, y: 0.48, w: 1.65, h: 0.52 }, "示例数据标识");
  addText(s, manifest, id, "仅用于说明机制，不代表真实团队", { x: 8.00, y: 1.66, w: 4.50, h: 0.22 }, "示例边界", { fontSize: 10.5, bold: true, color: T.colors.vermilion, align: "right", component: "data-boundary" });
  const chart = { x: 0.78, y: 1.92, w: 7.45, h: 4.40 };
  addRect(s, manifest, id, chart, T.colors.paper2, T.colors.line, "原生条形图绘图区", { lineWidth: 0.7, component: "chart-area" });
  addText(s, manifest, id, "返工人时（构造示例）", { x: 1.10, y: 2.18, w: 2.9, h: 0.28 }, "图表标题", { fontSize: 12, bold: true, color: T.colors.muted, component: "chart-title" });
  s.addChart("bar", [{ name: "返工人时", labels: ["先做三页切片", "直接做完整 6 页"], values: [7, 18] }], {
    x: 1.02, y: 2.48, w: 6.72, h: 3.20,
    showLegend: false, showTitle: false, showValue: true, showCatName: false,
    showSerName: false, showPercent: false, showLeaderLines: false,
    showValAxisTitle: true, valAxisTitle: "单位：人时", showCatAxisTitle: false,
    valAxisMinVal: 0,
    catAxisLabelFontFace: T.fonts.body, catAxisLabelFontSize: 10,
    valAxisLabelFontFace: T.fonts.body, valAxisLabelFontSize: 9,
    chartColors: [T.colors.forest2, T.colors.vermilion], varyColors: true,
    dataLabelPosition: "inEnd", dataLabelColor: T.colors.white,
    barDir: "bar", catAxisLabelRotate: 0, gapWidthPct: 72
  });
  register(manifest, id, "native-chart", { x: 1.02, y: 2.48, w: 6.72, h: 3.20 }, "返工人时示例原生条形图");
  addText(s, manifest, id, "差异来自返工范围，\n不是制作速度承诺", { x: 8.74, y: 2.14, w: 3.50, h: 0.84 }, "图表解释", { fontSize: 21, bold: true, color: T.colors.forest, component: "chart-interpretation" });
  const notes = ["切片流程：3 页修正 + 复验", "直接全量：6 页返工 + 统一重排"];
  notes.forEach((n, i) => {
    addText(s, manifest, id, `0${i + 1}`, { x: 8.76, y: 3.40 + i * 0.74, w: 0.40, h: 0.24 }, "解释编号", { fontSize: 10.5, bold: true, color: T.colors.vermilion, component: "explain-number" });
    addLine(s, manifest, id, { x: 9.24, y: 3.52 + i * 0.74, w: 0.40, h: 0 }, T.colors.line, "解释引导", { width: 0.8, component: "explain-rule" });
    addText(s, manifest, id, n, { x: 9.76, y: 3.30 + i * 0.74, w: 2.76, h: 0.42 }, "构成说明", { fontSize: 12.5, color: T.colors.ink, valign: "mid", component: "explain-text" });
  });
  addRect(s, manifest, id, { x: 8.70, y: 5.18, w: 3.82, h: 1.10 }, "F8E9E4", "E8B6A9", "限制说明", { lineWidth: 0.8, component: "caveat-box" });
  addText(s, manifest, id, "所有数值均为构造示例；\n正式门禁不以该比例承诺收益。", { x: 8.98, y: 5.45, w: 3.26, h: 0.56 }, "限制说明文本", { fontSize: 11.5, bold: true, color: T.colors.vermilion, valign: "mid", component: "caveat-text" });
  addFooter(s, manifest, id, "来源：SRC-004（示例数据）"); s.addNotes(noteFor(spec, id));
}

function slide5(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S05"; const s = pptx.addSlide(); setBg(s); addTitle(s, manifest, id, "05/06", "DEFINITION OF DONE", "把审美争论改写成可验收的 Definition of Done");
  addText(s, manifest, id, "必须提交", { x: 0.78, y: 1.92, w: 2.1, h: 0.40 }, "提交列标题", { fontSize: 20, bold: true, color: T.colors.forest, component: "column-title" });
  addText(s, manifest, id, "必须检查", { x: 6.20, y: 1.92, w: 2.1, h: 0.40 }, "检查列标题", { fontSize: 20, bold: true, color: T.colors.forest, component: "column-title" });
  const submit = ["3 页可编辑 PPTX", "真实 Office 渲染图", "结构化批准记录"];
  submit.forEach((v, i) => {
    const y = 2.62 + i * 0.88;
    addText(s, manifest, id, `0${i + 1}`, { x: 0.82, y, w: 0.42, h: 0.30 }, "提交编号", { fontSize: 10.5, bold: true, color: T.colors.vermilion, component: "list-number" });
    addLine(s, manifest, id, { x: 1.34, y: y + 0.14, w: 0.62, h: 0 }, T.colors.line, "列表引导", { width: 0.8, component: "list-rule" });
    addText(s, manifest, id, v, { x: 2.10, y: y - 0.08, w: 3.15, h: 0.46 }, "提交项", { fontSize: 17, bold: true, color: T.colors.ink, valign: "mid", component: "submit-item" });
  });
  const checks = ["一页一结论", "字体与母题一致", "图表口径与标注", "无溢出 / 遮挡 / 占位"];
  checks.forEach((v, i) => {
    const y = 2.62 + i * 0.68;
    addText(s, manifest, id, `0${i + 1}`, { x: 6.24, y, w: 0.42, h: 0.26 }, "检查编号", { fontSize: 10.5, bold: true, color: T.colors.vermilion, component: "list-number" });
    addText(s, manifest, id, v, { x: 6.84, y: y - 0.08, w: 4.82, h: 0.40 }, "检查项", { fontSize: 16, color: T.colors.ink, valign: "mid", component: "check-item" });
    addLine(s, manifest, id, { x: 6.84, y: y + 0.40, w: 4.96, h: 0 }, T.colors.line, "检查分隔", { width: 0.6, component: "check-rule" });
  });
  addRect(s, manifest, id, { x: 0.78, y: 5.52, w: 11.76, h: 0.82 }, T.colors.forest, T.colors.forest, "阻断条件", { lineWidth: 0, component: "block-band" });
  addText(s, manifest, id, "BLOCK", { x: 1.08, y: 5.77, w: 1.1, h: 0.28 }, "阻断标签", { fontSize: 13, bold: true, color: "F5B5A5", valign: "mid", component: "block-label" });
  addText(s, manifest, id, "任一代表页方向未通过，不得进入全量构建", { x: 2.34, y: 5.70, w: 6.50, h: 0.36 }, "阻断规则", { fontSize: 17, bold: true, color: T.colors.white, valign: "mid", component: "block-rule" });
  addText(s, manifest, id, "判断方向是否可复制，\n不是把三页磨到最终像素。", { x: 9.04, y: 5.67, w: 3.12, h: 0.40 }, "门禁边界", { fontSize: 10.5, color: "D9E2DE", align: "right", valign: "mid", component: "gate-boundary" });
  addFooter(s, manifest, id, "来源：SRC-002 · SRC-003"); s.addNotes(noteFor(spec, id));
}

function slide6(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S06"; const s = pptx.addSlide(); setBg(s, T.colors.forest); addTitle(s, manifest, id, "06/06", "DECISION", "今天批准一条规则：切片未 PASS，不做全量", true);
  addText(s, manifest, id, "批准将“三页纵向切片 PASS”设为\n正式汇报全量构建的放行条件", { x: 0.80, y: 1.92, w: 7.32, h: 1.36 }, "批准请求", { fontSize: 28, bold: true, color: T.colors.white, component: "ask" });
  addStamp(s, manifest, id, "请求批准", { x: 10.46, y: 1.72, w: 1.98, h: 0.66 }, "批准校样章", true);
  const items = [
    ["01", "范围", "封面 + 最复杂机制页 + 数据/总结页"],
    ["02", "证据", "可编辑源稿 + 真实渲染 + QA 记录"],
    ["03", "试运行", "下一次正式技术汇报先执行一轮"]
  ];
  items.forEach((it, i) => {
    const y = 3.88 + i * 0.66;
    addText(s, manifest, id, it[0], { x: 0.84, y, w: 0.42, h: 0.24 }, "承诺编号", { fontSize: 10.5, bold: true, color: "F5B5A5", component: "commit-number" });
    addText(s, manifest, id, it[1], { x: 1.48, y: y - 0.06, w: 1.10, h: 0.34 }, "承诺类别", { fontSize: 14, bold: true, color: T.colors.white, valign: "mid", component: "commit-label" });
    addText(s, manifest, id, it[2], { x: 2.82, y: y - 0.06, w: 5.20, h: 0.34 }, "承诺内容", { fontSize: 13.5, color: "DCE6E1", valign: "mid", component: "commit-text" });
    addLine(s, manifest, id, { x: 1.42, y: y + 0.38, w: 6.60, h: 0 }, "557268", "承诺分隔", { width: 0.7, component: "commit-rule" });
  });
  addRect(s, manifest, id, { x: 8.96, y: 3.52, w: 3.46, h: 2.24 }, T.colors.paper, T.colors.paper, "决策规则面板", { lineWidth: 0, component: "decision-panel" });
  addText(s, manifest, id, "放行规则", { x: 9.28, y: 3.86, w: 1.48, h: 0.24 }, "规则标签", { fontSize: 11, bold: true, color: T.colors.vermilion, charSpacing: 1, component: "rule-label" });
  addText(s, manifest, id, "SLICE PASS", { x: 9.26, y: 4.36, w: 2.74, h: 0.38 }, "规则前件", { fontSize: 23, bold: true, color: T.colors.forest, component: "rule-condition" });
  addArrow(s, manifest, id, 9.30, 5.12, 1.02, T.colors.vermilion);
  addText(s, manifest, id, "FULL BUILD", { x: 10.50, y: 4.98, w: 1.52, h: 0.32 }, "规则后件", { fontSize: 13, bold: true, color: T.colors.vermilion, valign: "mid", component: "rule-action" });
  addText(s, manifest, id, "下一次正式技术汇报 / 先试运行一轮", { x: 0.82, y: 6.42, w: 5.8, h: 0.28 }, "下一步", { fontSize: 12, bold: true, color: "BFD1C9", component: "next-step" });
  addFooter(s, manifest, id, "来源：SRC-001 · SRC-002", true); s.addNotes(noteFor(spec, id));
}

const BUILDERS: Record<string, Function> = { S01: slide1, S02: slide2, S03: slide3, S04: slide4, S05: slide5, S06: slide6 };

async function main() {
  const args = parseArgs(process.argv.slice(2)); if (args.help) { usage(); return; }
  if (!args.spec || !args.output || !args.manifest) throw new Error("--spec, --output and --manifest are required");
  const specPath = path.resolve(String(args.spec)); const outPath = path.resolve(String(args.output)); const manifestPath = path.resolve(String(args.manifest));
  const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
  const selected = args.slides ? String(args.slides).split(",").map((x) => x.trim()).filter(Boolean) : spec.slides.map((x: any) => x.slide_id);
  const unknown = selected.filter((id) => !BUILDERS[id]); if (unknown.length) throw new Error(`Unknown slide ids: ${unknown.join(",")}`);
  const PptxGenJS = loadPptxGenJS(); const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE"; pptx.author = "Codex"; pptx.company = ""; pptx.subject = "发布门禁提案"; pptx.title = spec.deck.title; pptx.lang = "zh-CN";
  pptx.theme = { headFontFace: T.fonts.head, bodyFontFace: T.fonts.body, lang: "zh-CN" };
  pptx.defineSlideMaster({ title: "EDITORIAL_MASTER", background: { color: T.colors.paper }, objects: [], slideNumber: { x: 12.18, y: 7.08, w: 0.54, h: 0.16, fontFace: T.fonts.body, fontSize: 9, color: T.colors.muted, align: "right", margin: 0 } });
  const manifest: GeometryItem[] = [];
  selected.forEach((id) => BUILDERS[id](pptx, manifest, spec));
  fs.mkdirSync(path.dirname(outPath), { recursive: true }); await pptx.writeFile({ fileName: outPath, compression: true });
  const counts = manifest.reduce((a: Record<string, number>, x) => { a[x.component] = (a[x.component] || 0) + 1; return a; }, {});
  const report = { slide_size: T.slide, source_spec: specPath, output: outPath, slide_ids: selected, object_counts: counts, total_objects: manifest.length, elements: manifest };
  fs.writeFileSync(manifestPath, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify({ output: outPath, manifest: manifestPath, slides: selected.length, objects: manifest.length }));
}

main().catch((error) => { console.error(`ERROR: ${error.stack || error.message}`); process.exitCode = 1; });
