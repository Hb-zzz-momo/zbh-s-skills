import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { T } from "./theme.ts";
import {
  addArrow,
  addCodePanel,
  addFooter,
  addLine,
  addMicroHeader,
  addRect,
  addStamp,
  addText,
  type GeometryItem,
} from "./components.ts";

function loadPptxGenJS() {
  const localRequire = createRequire(import.meta.url);
  try {
    return localRequire("pptxgenjs");
  } catch {
    return createRequire("C:/Users/zbh/.agents/skills/presentation/pptx-builder-zh/package.json")("pptxgenjs");
  }
}

function parseArgs(argv: string[]) {
  const args: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--help" || argv[i] === "-h") args.help = true;
    else if (argv[i].startsWith("--")) {
      if (!argv[i + 1] || argv[i + 1].startsWith("--")) throw new Error(`Missing value for ${argv[i]}`);
      args[argv[i].slice(2)] = argv[++i];
    }
  }
  return args;
}

function usage() {
  console.log("tsx build.ts --spec slide-spec.json --output presentation.pptx --manifest build-manifest.json [--slides S01,S06,S08]");
}

function getSpec(spec: any, id: string) {
  const found = spec.slides.find((slide: any) => slide.slide_id === id);
  if (!found) throw new Error(`Missing slide contract: ${id}`);
  return found;
}

function setBg(slide: any, color: string) {
  slide.background = { color };
}

function addNotes(slide: any, spec: any, id: string) {
  slide.addNotes(getSpec(spec, id).speaker_notes || "");
}

function addHero(slide: any, manifest: GeometryItem[], id: string, title: string, dark = false, box: any = {}) {
  addText(slide, manifest, id, title, {
    x: box.x ?? 0.38,
    y: box.y ?? 0.36,
    w: box.w ?? 8.7,
    h: box.h ?? 1.22,
  }, "页面主标题", {
    fontFace: T.fonts.head,
    fontSize: box.fontSize ?? T.sizes.title,
    bold: true,
    color: dark ? T.colors.white : T.colors.ink,
    component: "hero-title",
  });
}

function slide1(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S01";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.black);
  addMicroHeader(slide, manifest, id, "01", "VIBE CODING PLAYBOOK", true);
  addText(slide, manifest, id, ss.claim, { x: 0.38, y: 0.45, w: 7.25, h: 1.55 }, "封面主标题", {
    fontFace: T.fonts.head, fontSize: 42, bold: true, color: T.colors.white, component: "cover-title",
  });
  addText(slide, manifest, id, "用 AI 加速构建，\n用证据守住质量", { x: 0.48, y: 2.68, w: 4.3, h: 0.72 }, "封面副标题", {
    fontSize: 17, bold: true, color: T.colors.white, component: "cover-subtitle",
  });
  addText(slide, manifest, id, "BEGINNER PLAYBOOK", { x: 0.48, y: 3.62, w: 2.75, h: 0.24 }, "课程标签", {
    fontFace: T.fonts.latin, fontSize: 9, bold: true, color: "B8BFC5", charSpacing: 1.5, component: "cover-tag",
  });
  addCodePanel(slide, manifest, id, { x: 8.33, y: 1.26, w: 4.55, h: 4.78 }, "AI CODING SESSION", [
    "> goal: filter unfinished tasks",
    "read src/TodoList.tsx",
    "edit query: status=open",
    "run npm test -- TodoList",
    "✓ open / done / empty",
    "review diff: 18 lines",
    "ready for human approval",
  ]);
  addLine(slide, manifest, id, { x: 7.76, y: 0.58, w: 0.30, h: 0 }, T.colors.white, "斜向入口箭头", { width: 1.1, component: "cover-arrow-a" });
  addLine(slide, manifest, id, { x: 8.06, y: 0.58, w: 0, h: 0.30 }, T.colors.white, "斜向入口箭头", { width: 1.1, component: "cover-arrow-b" });
  addText(slide, manifest, id, "VIBE / CODE", { x: 0.38, y: 6.47, w: 2.2, h: 0.32 }, "品牌落款", {
    fontFace: T.fonts.latin, fontSize: 18, bold: true, color: T.colors.white, component: "cover-brand",
  });
  addText(slide, manifest, id, "快速反馈，不放弃判断", { x: 8.34, y: 6.43, w: 4.54, h: 0.28 }, "封面结论", {
    fontSize: 11, color: "B8BFC5", align: "right", component: "cover-line",
  });
  addFooter(slide, manifest, id, ss.source_footer, true);
  addNotes(slide, spec, id);
}

function slide2(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S02";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.blue);
  addMicroHeader(slide, manifest, id, "02", "COURSE MAP", true);
  addHero(slide, manifest, id, ss.claim, true, { x: 0.38, y: 0.38, w: 5.4, h: 1.28, fontSize: 34 });
  const topics = [
    ["01", "重新定义"], ["02", "三个常见误区"], ["03", "小步闭环"],
    ["04", "提示与上下文"], ["05", "质量与安全"], ["06", "十分钟练习"],
  ];
  topics.forEach((item, i) => {
    const col = i < 3 ? 0 : 1;
    const row = i % 3;
    const x = 4.62 + col * 3.65;
    const y = 3.02 + row * 0.67;
    addText(slide, manifest, id, item[0], { x, y, w: 0.42, h: 0.24 }, "目录编号", {
      fontFace: T.fonts.latin, fontSize: 9, bold: true, color: T.colors.white, component: "toc-number",
    });
    addLine(slide, manifest, id, { x: x + 0.52, y: y + 0.11, w: 0.28, h: 0 }, "A8C7F4", "目录引导线", { width: 0.8, component: "toc-rule" });
    addText(slide, manifest, id, item[1], { x: x + 0.94, y: y - 0.04, w: 2.35, h: 0.30 }, "目录条目", {
      fontSize: 13, color: T.colors.white, component: "toc-item",
    });
  });
  addText(slide, manifest, id, "从定义到发布门禁，\n建立可迁移的协作方法。", { x: 0.48, y: 4.72, w: 3.3, h: 0.72 }, "课程地图说明", {
    fontSize: 15, bold: true, color: T.colors.white, component: "toc-summary",
  });
  addLine(slide, manifest, id, { x: 0.43, y: 6.06, w: 0.28, h: 0.28 }, T.colors.white, "目录角箭头", { width: 1.2, component: "corner-arrow" });
  addLine(slide, manifest, id, { x: 0.43, y: 6.06, w: 0.28, h: 0 }, T.colors.white, "目录角箭头", { width: 1.2, component: "corner-arrow" });
  addFooter(slide, manifest, id, ss.source_footer, true);
  addNotes(slide, spec, id);
}

function slide3(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S03";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.paper);
  addMicroHeader(slide, manifest, id, "03", "DEFINITION", false);
  addHero(slide, manifest, id, ss.claim, false, { x: 0.38, y: 0.35, w: 7.25, h: 1.20, fontSize: 30 });
  addText(slide, manifest, id, "自然语言只是入口，\n反馈闭环才是差异", { x: 4.88, y: 1.46, w: 3.18, h: 0.78 }, "定义主张", {
    fontSize: 18, bold: true, color: T.colors.ink, component: "definition-line",
  });
  addText(slide, manifest, id, "different", { x: 4.88, y: 2.30, w: 1.35, h: 0.24 }, "蓝色强调词", {
    fontFace: T.fonts.latin, fontSize: 13, bold: true, color: T.colors.blue, component: "definition-accent",
  });
  const principles = [
    ["↘", "自然语言起步", "先表达意图，再进入实现细节"],
    ["↘", "高频反馈", "生成、运行、观察、修正"],
    ["↘", "人类负责", "目标、边界、验证、发布"],
  ];
  principles.forEach((p, i) => {
    const x = 8.22 + i * 1.58;
    addText(slide, manifest, id, p[0], { x, y: 1.52, w: 0.26, h: 0.22 }, "原则箭头", { fontSize: 11, color: T.colors.blue, component: "principle-arrow" });
    addText(slide, manifest, id, p[1], { x, y: 1.84, w: 1.30, h: 0.38 }, "原则标题", { fontSize: 10.5, bold: true, color: T.colors.ink, component: "principle-label" });
    addText(slide, manifest, id, p[2], { x, y: 2.25, w: 1.35, h: 0.58 }, "原则说明", { fontSize: 8.5, color: T.colors.muted, component: "principle-detail" });
  });
  addCodePanel(slide, manifest, id, { x: 0.48, y: 3.25, w: 3.98, h: 2.50 }, "INTENT", [
    "goal: unfinished filter",
    "context: existing TodoList",
    "constraint: no DB change",
    "done: tests + screenshot",
  ]);
  addCodePanel(slide, manifest, id, { x: 4.70, y: 3.25, w: 3.98, h: 2.50 }, "FEEDBACK", [
    "run → observe",
    "test failed: empty state",
    "fix component branch",
    "rerun → 3 tests pass",
  ], true);
  addCodePanel(slide, manifest, id, { x: 8.92, y: 3.25, w: 3.94, h: 2.50 }, "JUDGMENT", [
    "review diff",
    "check permissions",
    "verify acceptance criteria",
    "human approves release",
  ]);
  addFooter(slide, manifest, id, ss.source_footer, false);
  addNotes(slide, spec, id);
}

function slide4(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S04";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.blue);
  addMicroHeader(slide, manifest, id, "04", "BOUNDARY", true);
  addHero(slide, manifest, id, ss.claim, true, { x: 0.38, y: 0.35, w: 7.5, h: 1.25, fontSize: 30 });
  addText(slide, manifest, id, "FAST\nFEEDBACK", { x: 0.78, y: 2.62, w: 3.2, h: 1.06 }, "价值关键词", {
    fontFace: T.fonts.latin, fontSize: 30, bold: true, color: T.colors.white, component: "value-keyword",
  });
  addText(slide, manifest, id, "速度优势只在反馈可观察、\n修改可回滚时成立。", { x: 0.82, y: 4.12, w: 3.65, h: 0.64 }, "边界结论", {
    fontSize: 14.5, bold: true, color: T.colors.white, component: "boundary-summary",
  });
  addRect(slide, manifest, id, { x: 5.12, y: 2.30, w: 3.34, h: 3.42 }, T.colors.paper, T.colors.paper, "适用区域", { lineWidth: 0, component: "fit-area" });
  addText(slide, manifest, id, "适用 / FIT", { x: 5.42, y: 2.62, w: 1.72, h: 0.34 }, "适用标题", {
    fontSize: 17, bold: true, color: T.colors.blue, component: "fit-title",
  });
  ["原型与交互验证", "内部工具与重复脚本", "低风险、可撤销界面"].forEach((v, i) => {
    addText(slide, manifest, id, `0${i + 1}`, { x: 5.42, y: 3.25 + i * 0.60, w: 0.35, h: 0.20 }, "适用编号", { fontSize: 8.5, bold: true, color: T.colors.blue, component: "fit-number" });
    addText(slide, manifest, id, v, { x: 5.92, y: 3.17 + i * 0.60, w: 2.10, h: 0.30 }, "适用场景", { fontSize: 11.5, color: T.colors.ink, component: "fit-item" });
  });
  addRect(slide, manifest, id, { x: 8.72, y: 2.30, w: 4.08, h: 3.42 }, T.colors.black, T.colors.black, "慎用区域", { lineWidth: 0, component: "caution-area" });
  addText(slide, manifest, id, "慎用 / CAUTION", { x: 9.04, y: 2.62, w: 2.36, h: 0.34 }, "慎用标题", {
    fontSize: 17, bold: true, color: T.colors.white, component: "caution-title",
  });
  ["认证、支付与权限", "隐私、核心数据与秘密", "不可逆操作与关键基础设施"].forEach((v, i) => {
    addText(slide, manifest, id, `0${i + 1}`, { x: 9.04, y: 3.25 + i * 0.60, w: 0.35, h: 0.20 }, "慎用编号", { fontSize: 8.5, bold: true, color: "BFD4FF", component: "caution-number" });
    addText(slide, manifest, id, v, { x: 9.54, y: 3.17 + i * 0.60, w: 2.78, h: 0.30 }, "慎用场景", { fontSize: 11.5, color: T.colors.white, component: "caution-item" });
  });
  addArrow(slide, manifest, id, 4.70, 4.02, 0.28, T.colors.white, "fit-arrow");
  addFooter(slide, manifest, id, ss.source_footer, true);
  addNotes(slide, spec, id);
}

function slide5(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S05";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.paper);
  addMicroHeader(slide, manifest, id, "05", "FAILURE MODES", false);
  addHero(slide, manifest, id, ss.claim, false, { x: 0.38, y: 0.35, w: 7.4, h: 1.22, fontSize: 30 });
  const problems = [
    { no: "01", x: 0.52, y: 2.28, title: "愿望式提示", body: "只说做什么，\n不说完成标准" },
    { no: "02", x: 4.38, y: 3.03, title: "上下文断裂", body: "模型不知道项目约定\n和真实接口" },
    { no: "03", x: 8.42, y: 3.78, title: "跳过验证", body: "能运行，\n就当成可以发布" },
  ];
  problems.forEach((p) => {
    addText(slide, manifest, id, p.no, { x: p.x, y: p.y, w: 1.28, h: 0.90 }, "问题编号", {
      fontFace: T.fonts.latin, fontSize: 48, color: T.colors.blue, component: "problem-number",
    });
    addText(slide, manifest, id, p.title, { x: p.x + 1.43, y: p.y + 0.10, w: 1.90, h: 0.28 }, "问题标题", {
      fontSize: 12.5, bold: true, color: T.colors.ink, component: "problem-title",
    });
    addText(slide, manifest, id, p.body, { x: p.x + 1.43, y: p.y + 0.48, w: 2.26, h: 0.58 }, "问题描述", {
      fontSize: 10.5, color: T.colors.muted, component: "problem-detail",
    });
    addText(slide, manifest, id, "↘", { x: p.x + 1.43, y: p.y + 1.08, w: 0.30, h: 0.22 }, "问题箭头", {
      fontSize: 11, color: T.colors.ink, component: "problem-arrow",
    });
  });
  addLine(slide, manifest, id, { x: 0.52, y: 6.30, w: 0.24, h: 0 }, T.colors.blue, "结论引导线", { width: 2, component: "takeaway-rule" });
  addText(slide, manifest, id, "多数失败不是模型不会写，而是目标、上下文、验证缺了一环。", { x: 0.52, y: 6.47, w: 8.1, h: 0.30 }, "失败模式结论", {
    fontSize: 12.5, bold: true, color: T.colors.ink, component: "takeaway",
  });
  addFooter(slide, manifest, id, ss.source_footer, false);
  addNotes(slide, spec, id);
}

function slide6(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S06";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.blue);
  addMicroHeader(slide, manifest, id, "06", "METHOD", true);
  addHero(slide, manifest, id, ss.claim, true, { x: 0.38, y: 0.35, w: 6.7, h: 1.18, fontSize: 30 });
  addText(slide, manifest, id, "每次只推进一个可观察切片", { x: 7.56, y: 1.15, w: 4.68, h: 0.38 }, "流程主张", {
    fontSize: 15.5, bold: true, color: T.colors.white, align: "right", component: "loop-summary",
  });
  const steps = [
    ["01", "定义", "目标 + Done"], ["02", "给上下文", "文件 + 约束"], ["03", "生成", "一个薄切片"],
    ["04", "验证", "运行 + 测试"], ["05", "修复", "回源再复验"],
  ];
  steps.forEach((st, i) => {
    const x = 0.48 + i * 2.53;
    const y = 2.30 + (i % 2 === 0 ? 0 : 0.34);
    addRect(slide, manifest, id, { x, y, w: 2.08, h: 1.54 }, i === 2 ? T.colors.black : T.colors.paper, i === 2 ? T.colors.black : T.colors.paper, `步骤 ${st[1]}`, { lineWidth: 0, component: "loop-step" });
    addText(slide, manifest, id, st[0], { x: x + 0.18, y: y + 0.17, w: 0.36, h: 0.22 }, "步骤编号", {
      fontFace: T.fonts.latin, fontSize: 9, bold: true, color: i === 2 ? "BFD4FF" : T.colors.blue, component: "loop-number",
    });
    addText(slide, manifest, id, st[1], { x: x + 0.18, y: y + 0.52, w: 1.68, h: 0.33 }, "步骤标题", {
      fontSize: 16, bold: true, color: i === 2 ? T.colors.white : T.colors.ink, component: "loop-title",
    });
    addText(slide, manifest, id, st[2], { x: x + 0.18, y: y + 1.03, w: 1.68, h: 0.25 }, "步骤产物", {
      fontSize: 9.5, color: i === 2 ? "AAB1B7" : T.colors.muted, component: "loop-detail",
    });
    if (i < steps.length - 1) addArrow(slide, manifest, id, x + 2.12, y + 0.76, 0.31, T.colors.white, "loop-arrow");
  });
  addCodePanel(slide, manifest, id, { x: 0.48, y: 4.70, w: 3.82, h: 1.58 }, "DEFINE", [
    "Goal / Context",
    "Constraints / Done",
    "one behavior only",
  ]);
  addCodePanel(slide, manifest, id, { x: 4.76, y: 4.70, w: 3.82, h: 1.58 }, "VERIFY", [
    "npm test -- TodoList",
    "✓ open ✓ done ✓ empty",
    "capture evidence",
  ], true);
  addCodePanel(slide, manifest, id, { x: 9.04, y: 4.70, w: 3.80, h: 1.58 }, "FIX", [
    "failure → source file",
    "small diff → rerun",
    "approve only with proof",
  ]);
  addFooter(slide, manifest, id, ss.source_footer, true);
  addNotes(slide, spec, id);
}

function slide7(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S07";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.paper);
  addMicroHeader(slide, manifest, id, "07", "PROMPTING", false);
  addHero(slide, manifest, id, ss.claim, false, { x: 0.38, y: 0.35, w: 6.7, h: 1.18, fontSize: 30 });
  addText(slide, manifest, id, "好提示 = 一个可执行的产品简报", { x: 5.82, y: 1.43, w: 3.55, h: 0.42 }, "提示结论", {
    fontSize: 16, bold: true, color: T.colors.ink, component: "prompt-summary",
  });
  const formula = [
    ["01", "GOAL", "用户最终能做什么"],
    ["02", "CONTEXT", "现有文件、接口、约定"],
    ["03", "CONSTRAINTS", "不能改什么、技术边界"],
    ["04", "DONE", "如何证明完成"],
  ];
  formula.forEach((it, i) => {
    const y = 2.25 + i * 0.91;
    addText(slide, manifest, id, it[0], { x: 0.50, y: y + 0.08, w: 0.36, h: 0.20 }, "公式编号", { fontSize: 8.5, bold: true, color: T.colors.blue, component: "formula-number" });
    addLine(slide, manifest, id, { x: 1.00, y: y + 0.17, w: 0.43, h: 0 }, T.colors.soft, "公式引导线", { width: 0.8, component: "formula-rule" });
    addText(slide, manifest, id, it[1], { x: 1.58, y, w: 1.68, h: 0.30 }, "公式标签", { fontFace: T.fonts.latin, fontSize: 12.5, bold: true, color: T.colors.blue, component: "formula-label" });
    addText(slide, manifest, id, it[2], { x: 3.24, y: y - 0.01, w: 2.28, h: 0.30 }, "公式说明", { fontSize: 11.5, color: T.colors.ink, component: "formula-detail" });
  });
  addRect(slide, manifest, id, { x: 6.18, y: 2.18, w: 6.62, h: 3.72 }, T.colors.black, T.colors.black, "提示示例面板", { lineWidth: 0, component: "prompt-panel" });
  addText(slide, manifest, id, "PROMPT CONTRACT", { x: 6.48, y: 2.46, w: 2.25, h: 0.24 }, "提示面板标签", { fontFace: T.fonts.latin, fontSize: 8.5, bold: true, color: "BFD4FF", charSpacing: 1.2, component: "prompt-label" });
  const lines = [
    ["Goal", "为待办页增加“未完成”筛选"],
    ["Context", "复用现有 TodoList 与查询 API"],
    ["Constraints", "不改数据库，不新增依赖"],
    ["Done", "3 条测试通过 + 运行截图 + 小 Diff"],
  ];
  lines.forEach((line, i) => {
    const y = 3.02 + i * 0.63;
    addText(slide, manifest, id, `${line[0]}:`, { x: 6.48, y, w: 1.10, h: 0.26 }, "提示字段", { fontFace: T.fonts.mono, fontSize: 10.5, bold: true, color: T.colors.white, component: "prompt-field" });
    addText(slide, manifest, id, line[1], { x: 7.70, y, w: 4.62, h: 0.30 }, "提示内容", { fontSize: 11.5, color: i === 3 ? "BFD4FF" : "C5CBD0", component: "prompt-value" });
  });
  addStamp(slide, manifest, id, "可验证", { x: 10.78, y: 5.20, w: 1.38, h: 0.48 }, true);
  addFooter(slide, manifest, id, ss.source_footer, false);
  addNotes(slide, spec, id);
}

function slide8(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S08";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.blue);
  addMicroHeader(slide, manifest, id, "08", "DEMO", true);
  addHero(slide, manifest, id, ss.claim, true, { x: 0.38, y: 0.35, w: 7.1, h: 1.18, fontSize: 30 });
  addText(slide, manifest, id, "逐轮收窄，不赌一句万能提示", { x: 8.38, y: 1.19, w: 4.35, h: 0.34 }, "演示结论", {
    fontSize: 14.5, bold: true, color: T.colors.white, align: "right", component: "demo-summary",
  });
  addCodePanel(slide, manifest, id, { x: 0.48, y: 2.10, w: 3.85, h: 3.28 }, "01 / PROMPT", [
    "Goal: unfinished filter",
    "Context: TodoList.tsx",
    "Constraint: no DB change",
    "Done: tests + screenshot",
    "scope locked",
  ]);
  addCodePanel(slide, manifest, id, { x: 4.74, y: 2.48, w: 3.85, h: 3.10 }, "02 / BUILD", [
    "edit TodoList.tsx",
    "+ status query parameter",
    "+ empty-state branch",
    "18 lines changed",
    "run local preview",
  ], true);
  addCodePanel(slide, manifest, id, { x: 9.00, y: 2.86, w: 3.84, h: 3.42 }, "03 / VERIFY", [
    "✓ open tasks",
    "✓ completed tasks",
    "✕ empty state spacing",
    "fix → rerun",
    "✓ 3/3 + screenshot",
  ]);
  addArrow(slide, manifest, id, 4.37, 3.92, 0.27, T.colors.white, "demo-arrow");
  addArrow(slide, manifest, id, 8.63, 4.30, 0.27, T.colors.white, "demo-arrow");
  addFooter(slide, manifest, id, ss.source_footer, true);
  addNotes(slide, spec, id);
}

function slide9(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S09";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.paper);
  addMicroHeader(slide, manifest, id, "09", "CONTEXT", false);
  addHero(slide, manifest, id, ss.claim, false, { x: 0.38, y: 0.35, w: 6.5, h: 1.18, fontSize: 30 });
  addText(slide, manifest, id, "项目文件比更长的提示\n更有复用价值", { x: 6.05, y: 1.15, w: 3.40, h: 0.74 }, "上下文主张", {
    fontSize: 18, bold: true, color: T.colors.ink, component: "context-summary",
  });
  const files = [
    ["README", "怎么运行", ["install", "start", "verify"]],
    ["AGENTS.md", "怎么协作", ["scope", "rules", "deliver"]],
    ["TESTS", "什么叫正确", ["happy", "edge", "failure"]],
    ["EXAMPLES", "项目真实风格", ["pattern", "naming", "output"]],
  ];
  files.forEach((f, i) => {
    const x = 0.48 + i * 3.10;
    const y = 3.05 + (i % 2 === 0 ? 0 : 0.24);
    addCodePanel(slide, manifest, id, { x, y, w: 2.76, h: 2.18 }, f[0] as string, f[2] as string[], i === 1 || i === 3);
    addText(slide, manifest, id, f[1] as string, { x, y: y + 2.36, w: 2.76, h: 0.28 }, "上下文文件作用", {
      fontSize: 11.5, bold: true, color: T.colors.ink, align: "center", component: "context-caption",
    });
  });
  addText(slide, manifest, id, "↘", { x: 0.48, y: 2.24, w: 0.30, h: 0.24 }, "上下文箭头", { fontSize: 12, color: T.colors.blue, component: "context-arrow" });
  addText(slide, manifest, id, "把重复规则写进仓库，\n让每一轮对话都从同一事实出发。", { x: 0.96, y: 2.18, w: 4.10, h: 0.58 }, "上下文说明", {
    fontSize: 12.5, color: T.colors.muted, component: "context-detail",
  });
  addFooter(slide, manifest, id, ss.source_footer, false);
  addNotes(slide, spec, id);
}

function slide10(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S10";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.paper);
  addMicroHeader(slide, manifest, id, "10", "QUALITY", false);
  addHero(slide, manifest, id, ss.claim, false, { x: 0.38, y: 0.35, w: 6.9, h: 1.18, fontSize: 30 });
  addText(slide, manifest, id, "必须验证", { x: 0.54, y: 2.05, w: 2.0, h: 0.36 }, "验证列标题", { fontSize: 18, bold: true, color: T.colors.blue, component: "gate-column" });
  addText(slide, manifest, id, "必须守住", { x: 6.75, y: 2.05, w: 2.0, h: 0.36 }, "安全列标题", { fontSize: 18, bold: true, color: T.colors.blue, component: "gate-column" });
  const left = [["01", "能运行", "真实入口可启动"], ["02", "有测试", "正常与失败路径"], ["03", "可审查", "Diff 小且可解释"]];
  left.forEach((it, i) => {
    const y = 2.77 + i * 0.86;
    addText(slide, manifest, id, it[0], { x: 0.55, y, w: 0.38, h: 0.23 }, "门禁编号", { fontSize: 9, bold: true, color: T.colors.blue, component: "gate-number" });
    addLine(slide, manifest, id, { x: 1.05, y: y + 0.11, w: 0.48, h: 0 }, T.colors.soft, "门禁引导线", { width: 0.8, component: "gate-rule" });
    addText(slide, manifest, id, it[1], { x: 1.70, y: y - 0.05, w: 1.35, h: 0.30 }, "门禁标题", { fontSize: 14, bold: true, color: T.colors.ink, component: "gate-title" });
    addText(slide, manifest, id, it[2], { x: 3.12, y: y - 0.04, w: 2.58, h: 0.30 }, "门禁说明", { fontSize: 11.5, color: T.colors.muted, component: "gate-detail" });
  });
  const right = [["01", "输入", "外部内容不可信"], ["02", "权限", "最小授权与确认"], ["03", "秘密与依赖", "不泄露、不盲装"]];
  right.forEach((it, i) => {
    const y = 2.77 + i * 0.86;
    addText(slide, manifest, id, it[0], { x: 6.76, y, w: 0.38, h: 0.23 }, "安全编号", { fontSize: 9, bold: true, color: T.colors.blue, component: "safety-number" });
    addLine(slide, manifest, id, { x: 7.26, y: y + 0.11, w: 0.48, h: 0 }, T.colors.soft, "安全引导线", { width: 0.8, component: "safety-rule" });
    addText(slide, manifest, id, it[1], { x: 7.91, y: y - 0.05, w: 1.62, h: 0.30 }, "安全标题", { fontSize: 14, bold: true, color: T.colors.ink, component: "safety-title" });
    addText(slide, manifest, id, it[2], { x: 9.64, y: y - 0.04, w: 2.70, h: 0.30 }, "安全说明", { fontSize: 11.5, color: T.colors.muted, component: "safety-detail" });
  });
  addRect(slide, manifest, id, { x: 0.54, y: 5.64, w: 12.26, h: 0.72 }, T.colors.black, T.colors.black, "质量门禁结论条", { lineWidth: 0, component: "quality-band" });
  addText(slide, manifest, id, "模型输出 = 未验证候选实现", { x: 0.88, y: 5.84, w: 4.72, h: 0.30 }, "质量门禁结论", {
    fontSize: 17, bold: true, color: T.colors.white, component: "quality-conclusion",
  });
  addText(slide, manifest, id, "发布决定始终由人负责", { x: 8.90, y: 5.86, w: 3.48, h: 0.26 }, "发布责任", {
    fontSize: 11.5, color: "BFD4FF", align: "right", component: "quality-owner",
  });
  addFooter(slide, manifest, id, ss.source_footer, false);
  addNotes(slide, spec, id);
}

function slide11(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S11";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.blue);
  addMicroHeader(slide, manifest, id, "11", "LAB", true);
  addHero(slide, manifest, id, ss.claim, true, { x: 0.38, y: 0.35, w: 5.8, h: 1.18, fontSize: 30 });
  addText(slide, manifest, id, "10:00", { x: 0.56, y: 2.22, w: 3.42, h: 1.04 }, "练习计时器", {
    fontFace: T.fonts.latin, fontSize: 52, bold: true, color: T.colors.white, component: "lab-timer",
  });
  addText(slide, manifest, id, "只完成一个小闭环，\n不比赛谁写得多。", { x: 0.62, y: 3.57, w: 3.34, h: 0.62 }, "练习原则", {
    fontSize: 15, bold: true, color: T.colors.white, component: "lab-principle",
  });
  addRect(slide, manifest, id, { x: 4.72, y: 2.18, w: 4.02, h: 1.32 }, T.colors.paper, T.colors.paper, "练习任务", { lineWidth: 0, component: "lab-task" });
  addText(slide, manifest, id, "TASK", { x: 4.98, y: 2.42, w: 0.72, h: 0.22 }, "任务标签", { fontFace: T.fonts.latin, fontSize: 8.5, bold: true, color: T.colors.blue, component: "lab-label" });
  addText(slide, manifest, id, "为静态待办页增加\n“未完成”筛选", { x: 4.98, y: 2.75, w: 3.20, h: 0.52 }, "练习任务内容", { fontSize: 15.5, bold: true, color: T.colors.ink, component: "lab-task-text" });
  addRect(slide, manifest, id, { x: 8.98, y: 2.65, w: 3.82, h: 1.92 }, T.colors.black, T.colors.black, "练习交付物", { lineWidth: 0, component: "lab-deliverable" });
  addText(slide, manifest, id, "DELIVER", { x: 9.26, y: 2.93, w: 1.05, h: 0.22 }, "交付标签", { fontFace: T.fonts.latin, fontSize: 8.5, bold: true, color: "BFD4FF", component: "lab-label" });
  addText(slide, manifest, id, "1 段结构化提示\n1 个可运行切片\n3 条验证证据", { x: 9.26, y: 3.28, w: 2.90, h: 0.86 }, "练习交付物内容", { fontSize: 13.5, bold: true, color: T.colors.white, component: "lab-deliverable-text" });
  addRect(slide, manifest, id, { x: 4.72, y: 4.08, w: 4.02, h: 1.50 }, T.colors.blueDark, T.colors.white, "练习规则", { lineWidth: 0.8, component: "lab-rule" });
  addText(slide, manifest, id, "RULE", { x: 4.98, y: 4.35, w: 0.74, h: 0.22 }, "规则标签", { fontFace: T.fonts.latin, fontSize: 8.5, bold: true, color: T.colors.white, component: "lab-label" });
  addText(slide, manifest, id, "一次只改一个行为；\n失败必须保留并修复。", { x: 4.98, y: 4.72, w: 3.20, h: 0.58 }, "练习规则内容", { fontSize: 13, bold: true, color: T.colors.white, component: "lab-rule-text" });
  addStamp(slide, manifest, id, "START SMALL", { x: 10.12, y: 5.26, w: 1.84, h: 0.56 }, true);
  addFooter(slide, manifest, id, ss.source_footer, true);
  addNotes(slide, spec, id);
}

function slide12(pptx: any, manifest: GeometryItem[], spec: any) {
  const id = "S12";
  const ss = getSpec(spec, id);
  const slide = pptx.addSlide();
  setBg(slide, T.colors.black);
  addMicroHeader(slide, manifest, id, "12", "CLOSING", true);
  addText(slide, manifest, id, ss.claim, { x: 0.38, y: 0.42, w: 8.70, h: 1.30 }, "收束主标题", {
    fontFace: T.fonts.head, fontSize: 36, bold: true, color: T.colors.white, component: "closing-title",
  });
  addText(slide, manifest, id, "Vibe Coding 的价值来自更短反馈；\n它的安全来自人类保留判断。", { x: 0.72, y: 2.58, w: 5.35, h: 0.78 }, "收束说明", {
    fontSize: 18, bold: true, color: T.colors.white, component: "closing-summary",
  });
  addText(slide, manifest, id, "下一次编码，从一个\n可验证的薄切片开始。", { x: 0.72, y: 4.38, w: 5.40, h: 0.88 }, "行动句", {
    fontSize: 22, bold: true, color: "BFD4FF", component: "closing-action",
  });
  addRect(slide, manifest, id, { x: 8.42, y: 2.02, w: 4.30, h: 1.48 }, T.colors.paper, T.colors.paper, "AI 责任区", { lineWidth: 0, component: "ai-role" });
  addText(slide, manifest, id, "AI", { x: 8.74, y: 2.34, w: 0.58, h: 0.30 }, "AI 标签", { fontFace: T.fonts.latin, fontSize: 16, bold: true, color: T.colors.blue, component: "role-label" });
  addText(slide, manifest, id, "生成候选实现\n加速探索与修改", { x: 9.62, y: 2.28, w: 2.58, h: 0.62 }, "AI 责任", { fontSize: 14, bold: true, color: T.colors.ink, component: "role-detail" });
  addRect(slide, manifest, id, { x: 8.42, y: 3.78, w: 4.30, h: 1.82 }, T.colors.blue, T.colors.blue, "人类责任区", { lineWidth: 0, component: "human-role" });
  addText(slide, manifest, id, "HUMAN", { x: 8.74, y: 4.12, w: 1.10, h: 0.30 }, "人类标签", { fontFace: T.fonts.latin, fontSize: 14, bold: true, color: T.colors.white, component: "role-label" });
  addText(slide, manifest, id, "定义目标与边界\n审查证据\n批准发布", { x: 9.92, y: 4.04, w: 2.16, h: 0.92 }, "人类责任", { fontSize: 13.5, bold: true, color: T.colors.white, component: "role-detail" });
  addText(slide, manifest, id, "VIBE / CODE", { x: 0.38, y: 6.48, w: 2.2, h: 0.32 }, "品牌落款", {
    fontFace: T.fonts.latin, fontSize: 18, bold: true, color: T.colors.white, component: "closing-brand",
  });
  addLine(slide, manifest, id, { x: 7.80, y: 6.14, w: 0.30, h: 0.30 }, T.colors.white, "收束角箭头", { width: 1.2, component: "closing-arrow" });
  addLine(slide, manifest, id, { x: 7.80, y: 6.14, w: 0.30, h: 0 }, T.colors.white, "收束角箭头", { width: 1.2, component: "closing-arrow" });
  addFooter(slide, manifest, id, ss.source_footer, true);
  addNotes(slide, spec, id);
}

const BUILDERS: Record<string, (pptx: any, manifest: GeometryItem[], spec: any) => void> = {
  S01: slide1,
  S02: slide2,
  S03: slide3,
  S04: slide4,
  S05: slide5,
  S06: slide6,
  S07: slide7,
  S08: slide8,
  S09: slide9,
  S10: slide10,
  S11: slide11,
  S12: slide12,
};

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    return;
  }
  if (!args.spec || !args.output || !args.manifest) throw new Error("--spec, --output and --manifest are required");
  const specPath = path.resolve(String(args.spec));
  const outputPath = path.resolve(String(args.output));
  const manifestPath = path.resolve(String(args.manifest));
  const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
  const selected = args.slides
    ? String(args.slides).split(",").map((id) => id.trim()).filter(Boolean)
    : spec.slides.map((slide: any) => slide.slide_id);
  const unknown = selected.filter((id) => !BUILDERS[id]);
  if (unknown.length) throw new Error(`Unknown slide ids: ${unknown.join(", ")}`);

  const PptxGenJS = loadPptxGenJS();
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Codex";
  pptx.company = "";
  pptx.subject = "Vibe Coding 教学";
  pptx.title = spec.deck.title;
  pptx.lang = "zh-CN";
  pptx.theme = {
    headFontFace: T.fonts.head,
    bodyFontFace: T.fonts.body,
    lang: "zh-CN",
  };
  pptx.defineSlideMaster({
    title: "PITCH_MASTER",
    background: { color: T.colors.paper },
    objects: [],
    slideNumber: {
      x: 12.40, y: 7.14, w: 0.40, h: 0.14,
      fontFace: T.fonts.latin, fontSize: 7.5, color: T.colors.muted, align: "right", margin: 0,
    },
  });

  const manifest: GeometryItem[] = [];
  selected.forEach((id) => BUILDERS[id](pptx, manifest, spec));
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  await pptx.writeFile({ fileName: outputPath, compression: true });
  const counts = manifest.reduce((acc: Record<string, number>, item) => {
    acc[item.component] = (acc[item.component] || 0) + 1;
    return acc;
  }, {});
  const report = {
    slide_size: T.slide,
    source_spec: specPath,
    output: outputPath,
    slide_ids: selected,
    object_counts: counts,
    total_objects: manifest.length,
    elements: manifest,
  };
  fs.writeFileSync(manifestPath, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify({ output: outputPath, manifest: manifestPath, slides: selected.length, objects: manifest.length }));
}

main().catch((error) => {
  console.error(`ERROR: ${error.stack || error.message}`);
  process.exitCode = 1;
});
