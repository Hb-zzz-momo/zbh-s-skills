---
name: web-design-workflow-zh
description: "中文 Web Design 与 Vibe Coding 总控工作流：按新建网站、现有页面改版、图像先行和正式产品交付选择最少必要 skill，执行需求规格化、DESIGN.md、审美批判、纵向切片、工程实现、真实浏览器验收和上线门禁。Use when: 做网站、设计页面、landing page、portfolio、产品页、网站高级感、页面太丑、改版前端、生成 DESIGN.md、image-to-code、Vibe Coding、Web UI 验收、避免 AI 味、前端审美工作流。"
---

# Web Design Workflow Zh

## 目标

用一个总控入口编排 Web 设计和前端交付：

```text
需求边界 -> 选择任务分支 -> DESIGN.md -> 视觉纵向切片 -> 工程实现 -> 浏览器验收 -> 按需上线
```

该技能只负责路由和阶段门禁。不要一次性加载全部外部 skills；每个阶段只加载 1 个主 skill，最多追加 2 个辅助 skill。

## 启动检查

先读取当前项目的真实材料：

- `PRD.md` / `SPEC.md` / README / 用户提示词
- 现有 `DESIGN.md`、截图、Figma、参考 URL、品牌素材
- `package.json`、样式方案、组件库、路由和测试配置

再判断交付级别：

- **快速原型**：课程项目、Demo、比赛原型、MVP、单页展示。
- **正式产品**：真实上线、商业站点、SaaS、数据平台、长期维护项目。

详细步骤见 `references/workflow-modes.md`。

## 任务分支

### A. 新建网站 / 新页面

使用顺序：

```text
web-design 规则 -> frontend-design 批判 -> 本技能 Taste Gate
-> frontend-ui-engineering -> browser-testing-with-devtools -> Vercel Guidelines
```

产出项目根目录 `DESIGN.md`，再做一个代表全站质量的纵向切片，不要直接生成整站。

### B. 现有页面改版

使用顺序：

```text
redesign-existing-projects 审计 -> 更新 DESIGN.md
-> frontend-ui-engineering 定点修改 -> browser-testing-with-devtools 回归
```

先扫描、诊断、列出保留项，再修改。不得为了视觉重写框架、破坏业务行为或删除用户现有功能。

### C. 图像先行

仅在以下情况启用：

- 用户明确要求先出视觉稿、参考图或 image-to-code。
- 视觉辨识度是核心目标，文字规范不足以消除方向分歧。
- 当前环境有图像生成能力。

使用顺序：

```text
imagegen-frontend-web -> 选定视觉方向 -> image-to-code
-> DESIGN.md 反向固化 -> frontend-ui-engineering -> 浏览器验收
```

图像 skills 很长，只能放在独立设计阶段按需加载，不与完整 `taste-skill` 同时加载。

### D. 局部 UI Bug

沿用现有 `DESIGN.md` 或项目样式，不启动完整工作流。直接使用：

```text
frontend-ui-engineering -> browser-testing-with-devtools
```

### E. 单文件视觉产物

只有用户要单文件 HTML、浏览器演示、可交互视觉稿或 slide-like artifact 时，才考虑 `web-design-engineer`。普通产品前端不使用它替代项目工程流程。

## Phase 1: 规格化需求

至少锁定：

- 页面对象和唯一目标
- 目标用户与主要任务
- 页面/信息结构
- 真实内容和素材来源
- 现有技术栈或新项目最小技术选择
- 响应式、可访问性和验收范围

简单任务用一页 brief 即可；正式产品再扩展 PRD、用户流和页面结构。不要默认强制 Next.js、Tailwind 或 shadcn/ui，已有项目必须沿用现有栈。

## Phase 2: DESIGN.md 与审美门

先输出一行 Design Read：

```text
Reading this as: [页面类型] for [目标用户], with a [风格语言], leaning toward [设计系统/审美家族].
```

再确定：

- `DESIGN_VARIANCE`: 1-10，布局变化度。
- `MOTION_INTENSITY`: 1-10，动效强度。
- `VISUAL_DENSITY`: 1-10，信息密度。

创建或修订 `DESIGN.md`。契约见 `references/design-md-contract.md`。

### Taste Gate

在写代码前检查：

- 设计是否来自具体受众、内容和品牌，而不是“高级感”空话？
- 是否落入紫蓝渐变、米色奢华、黑底酸绿色、三等分卡片等默认模板？
- Hero 是否表达页面核心，而不是固定的 H1 + 副标题 + 双 CTA？
- 是否只有一个可解释的 signature moment，并让其余页面保持克制？
- 文案是否真实、具体、可操作？

未通过时先改 `DESIGN.md`，不要进入构建。

## Phase 3: 纵向切片

先实现一个能代表最终质量的完整片段，例如：

- Landing Page：导航 + Hero + 首个内容区。
- Dashboard：导航 + 一个真实数据区 + loading/empty/error。
- 表单流程：输入 + 校验 + 提交 + 成功/失败反馈。

切片必须同时覆盖真实内容、核心视觉、响应式和交互状态。方向错误时只返工切片，不返工整站。

协作模式下可展示切片让用户确认；用户要求自主端到端完成时，记录决策后继续，不停在等待确认。

## Phase 4: 工程实现

- 沿用项目框架、路由、样式方案和组件库。
- 新依赖前检查依赖文件，不假设库已安装。
- 颜色、字体、间距、圆角和动效来自 `DESIGN.md`。
- 组件保持单一职责，数据获取和展示分离。
- 覆盖 loading、empty、error、hover、focus、active 和 disabled。
- 按可验证切片推进，不一次生成整个复杂项目。
- 前端应用完成后启动 dev server，并提供本地 URL。

## Phase 5: 验收与交付

执行项目已有的 lint、typecheck、test、build，并做真实浏览器检查。至少覆盖桌面和移动端截图、控制台、网络、键盘导航、溢出和遮挡。

联网时读取最新 Vercel Web Interface Guidelines：

```text
https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
```

无法联网时使用 `references/acceptance-checklist.md`。发现问题要直接修正并复验。

正式产品再追加 code review、Preview Deployment、性能、SEO、安全和发布回滚门禁；快速原型不强制完整上线链。

## 压缩包技能读取

按 `references/source-map.md` 选择来源，并用脚本读取指定 entry：

```powershell
& .\scripts\Read-ZipSkill.ps1 -ZipPath C:\Users\zbh\.agents\skills-main.zip `
  -EntryPath skills-main/skills/frontend-design/SKILL.md
```

不得仅凭压缩包文件名推断内容。无效或下载不完整的 zip 不进入工作流。

## 输出要求

交付时说明：

- 使用了哪个任务分支和交付级别。
- PRD/brief、`DESIGN.md`、纵向切片和实现文件路径。
- 执行过的验证命令、浏览器视口和结果。
- 本地预览或 Preview URL。
- 未覆盖风险、缺失素材和正式上线前待办。

## 失败红线

- 不做任务分支判断就加载所有设计 skills。
- 新建整站时没有 `DESIGN.md` 或纵向切片就全面编码。
- 现有项目改版时先重写框架，再谈视觉。
- 把外部 skill 的固定字体、图标、技术栈当成高于项目约束的规则。
- 图像先行只生成漂亮图，不反向固化 token、组件状态和响应式规则。
- 只检查代码，不做真实浏览器截图和交互验证。
