---
name: web-design-workflow-zh
description: "中文 Web Design 工作流编排技能：把网站、页面、Landing Page、Portfolio、产品页和现有前端改版请求按 DESIGN.md 先行、审美守门、前端工程实现、真实浏览器与 Vercel Web Design Guidelines 验收四阶段推进。Use when: 做网站、设计页面、landing page、portfolio、产品页、网站高级感、页面太丑、改版前端、生成 DESIGN.md、Web UI 验收、避免 AI 味、前端审美工作流。"
---

# Web Design Workflow Zh

## 目标

把 Web 界面任务固定成一条可复用链路：

```
设计前 DESIGN.md -> 编码时审美守门 -> 工程化实现 -> 浏览器与规范验收
```

该技能是编排层，不替代具体项目实现。先用它锁定设计规范和验收口径，再按项目真实技术栈编码。

## 来源组合

| 阶段 | 主要来源 | 职责 |
|---|---|---|
| 设计前 | `KAOPU-XiaoPu/web-design` 本地压缩包 | 先产出可编辑的 `DESIGN.md`，定义颜色、字体、组件、动效和响应式规则 |
| 编码时 | `Leonxlnx/taste-skill` 本地压缩包 | 做 Design Read、三档审美参数和 anti-slop 守门，避免模板感、AI 味和廉价感 |
| 工程化 | 本地 `frontend-ui-engineering` | 组件结构、状态、响应式、可访问性、设计系统和真实工程约束 |
| 验收时 | Vercel Web Design Guidelines | 用最新 UI/UX/Accessibility 指南做最终审计；无法联网时使用本技能的本地验收清单 |

按需读取 `references/source-map.md` 了解源材料位置和加载策略。

## 工作流

### Step 0: 识别任务边界

先判断任务类型：

- 新页面 / 新网站：完整走 Step 1-5。
- 现有页面改丑：先做截图和代码审计，再走 Step 2-5。
- 只修一个 UI bug：沿用现有 `DESIGN.md` 或局部样式规范，不强行重建全站设计。
- 后端、数据库、纯逻辑 bug：不要使用本技能。

启动时检查项目根目录是否已有：

- `DESIGN.md`
- `PRD.md` / `SPEC.md`
- 截图、参考 URL、品牌素材、现有设计系统

信息不足且设计方向会明显分叉时，只问一个最关键的问题；能从上下文判断时直接继续。

### Step 1: Design Read

编码前先输出一行 Design Read：

```
Reading this as: [页面类型] for [目标用户], with a [风格语言], leaning toward [设计系统/审美家族].
```

然后锁定三个参数：

- `DESIGN_VARIANCE`: 1-10，布局变化度。
- `MOTION_INTENSITY`: 1-10，动效强度。
- `VISUAL_DENSITY`: 1-10，信息密度。

审美默认值不得无脑套用。必须根据目标用户、品牌、参考物、行业和使用场景调整。

### Step 2: 生成或修订 DESIGN.md

除非用户只要求局部 bug 修复，否则先创建或更新项目根目录的 `DESIGN.md`，再写代码。

`DESIGN.md` 必须覆盖 9 个章节：

1. Visual Theme & Atmosphere
2. Color Palette & Roles
3. Typography Rules
4. Component Stylings
5. Layout Principles
6. Depth & Elevation
7. Animation & Interaction
8. Do's and Don'ts
9. Responsive Behavior

详细契约见 `references/design-md-contract.md`。每章要有实质内容，不能只填模板标题。

### Step 3: Taste Gate

在编码前做一次 anti-slop 检查：

- 页面是否有具体受众和页面目标，而不是泛泛的“高级感”？
- 颜色、字体、布局是否来自本项目语境，而不是 AI 默认紫蓝渐变、奶油米色、高反差黑绿、三等分卡片？
- Hero 是否服务内容，而不是模板化大标题 + 副标题 + CTA？
- 是否有一个可解释的 signature moment，而不是到处撒动效？
- 文案是否真实可用，避免 lorem ipsum 式空话？

未通过时先改 `DESIGN.md`，不要直接写代码。

### Step 4: 工程化实现

编码时遵守：

- 先读现有项目结构、依赖、样式方案和组件库。
- 沿用项目技术栈；无项目时再选择最小可行方案。
- 新增依赖前查 `package.json`，不要假设库已安装。
- 组件保持单一职责，数据获取和展示分离。
- 颜色、字体、间距、圆角和动效必须来自 `DESIGN.md`。
- 每个交互元素必须有 hover、focus、active 和 disabled/不可用策略。
- 必须覆盖 loading、empty、error 状态，避免只做成功态。
- 移动端优先，至少检查 320px、768px、1024px、1440px。
- 避免大面积卡片套卡片、单色系 UI、文字溢出、元素重叠和无意义装饰。

如果是前端应用而不是静态文件，完成后启动本地 dev server，并把 URL 告诉用户。

### Step 5: 验收与修正

实现后必须跑可用的验证命令：

- 依赖安装状态检查
- lint / typecheck / test / build 中项目已有的质量门
- 真实浏览器检查，至少桌面和移动端视口
- 控制台错误、网络错误、横向滚动、文字溢出、遮挡、焦点态、键盘导航

联网可用时，验收前读取 Vercel 最新指南：

```
https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
```

无法联网时，使用 `references/acceptance-checklist.md` 作为本地降级清单。发现问题要直接修，不要只报告。

## 输出要求

交付时说明：

- `DESIGN.md` 是否新建或更新，以及路径。
- 实现涉及的关键文件。
- 已执行的验证命令和结果。
- 本地预览 URL。
- 未覆盖的风险或需要用户提供的素材。

## 失败红线

- 没有 `DESIGN.md` 就直接从零写整站。
- 把外部设计规则全量硬塞进代码，而不结合项目受众和内容。
- 用默认紫蓝渐变、米色奢华、三列卡片、毛玻璃堆叠制造“高级感”。
- 为了炫技引入无法维护的动效或大型依赖。
- 只在代码层完成，没做浏览器截图/真实视口验收。
