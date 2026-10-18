# 结论

你当前仓库中的 PPT 能力适合完成“故事线和页面规划”，但还不是一套完整的高级 PPT 生产系统。

建议将现有单一的：

```text
ppt-story-design-zh
```

升级为：

```text
ppt-workflow-orchestrator-zh
        │
        ├── ppt-story-design-zh          叙事与内容
        ├── ppt-visual-system-zh         视觉系统与版式
        ├── pptx-builder-zh              从零生成可编辑 PPTX
        ├── pptx-template-editor-zh      基于模板修改 PPTX
        ├── ppt-render-qa-zh             渲染、检查、修复
        └── ppt-data-storytelling-zh     图表与数据叙事
```

核心升级方向是：

> **从“PPT 大纲 Skill”升级为“证据—叙事—设计—构建—渲染—修复—交付”闭环。**

不建议一次加载所有 Skill。应继续遵循你仓库现有的路由原则：

```text
1 个主 Skill + 0～2 个阶段辅助 Skill + 必要验证
```

你仓库已经明确采用这种最小加载方式，并使用 Define → Plan → Build → Verify → Review → Ship 的工程生命周期，因此 PPT 总控 Skill 应复用这套体系。

---

# 1. 当前 PPT 工作流诊断

## 1.1 已经做得比较好的部分

现有 `ppt-story-design-zh` 已经覆盖：

- 听众识别
    
- 一句话主张
    
- 背景 → 痛点 → 方案 → 证据 → 价值 → 行动
    
- 一页只承担一个任务
    
- 证据补充
    
- 基础视觉方向
    
- 演讲顺序
    

这是正确的起点。

现有页面规划模板也已经包含：

```text
页码
页面标题
核心信息
建议图形
需要证据
演讲要点
```

说明仓库已经具备“逐页规划”的雏形。

## 1.2 当前最关键的缺口

### 缺口一：只有 Plan，没有 Build 和 Verify

当前路由中的 PPT 组合只有：

```text
ppt-story-design-zh
info-evidence-chain-zh
```

默认流程也仅为：

```text
先定故事线 → 补证据 → 页面结构 → 讲述顺序
```

没有 PPTX 构建、真实渲染、视觉验收和修复环节。

### 缺口二：页面规划模板信息不足

当前模板不能约束以下关键变量：

- 本页希望听众记住什么
    
- 本页希望听众采取什么行动
    
- 结论对应哪条证据
    
- 使用哪种页面版式
    
- 主视觉是什么
    
- 文字预算是多少
    
- 引用放在哪里
    
- 本页验收条件是什么
    

因此 AI 即使拿到页面列表，仍然可能自行发挥。

### 缺口三：没有视觉系统契约

现有 Skill 只要求选择“正式、科技、商业、教育、极简”等视觉方向，但这些词不足以指导页面生成。

需要增加类似 Web 工作流中 `DESIGN.md` 的 PPT 版本：

```text
PRESENTATION_DESIGN.md
```

你仓库的 Web Skill 已经使用了设计契约、Taste Gate（审美门禁）、纵向切片和真实浏览器验收，这套方法几乎可以原样迁移到 PPT。

### 缺口四：没有“从零创建”和“模板编辑”分支

高级 PPT 至少需要区分：

```text
A. 从零创建 PPTX
B. 基于现有模板替换内容
C. 修改已有 PPTX
D. 只输出大纲或视觉方案
```

这几种任务底层操作完全不同，不能共用一套执行逻辑。

### 缺口五：没有渲染—修复循环

目前没有明确要求：

```text
生成 PPTX
→ 转为 PDF
→ 转为逐页图片
→ 拼接缩略图
→ 视觉检查
→ 修复
→ 重新渲染
```

Anthropic 当前公开的生产级 PPTX Skill 也将文本提取、模板分析、PptxGenJS 创建、LibreOffice 渲染、Poppler 转图和至少一次修复—复验循环作为核心步骤。

---

# 2. 推荐的新 PPT 总工作流

```text
Phase 0  Intake
读取题目、材料、模板、品牌规范和交付要求
        ↓
Phase 1  Evidence
建立事实、数据、图片、案例和引用证据链
        ↓
Phase 2  Narrative
确定听众、目标、核心矛盾、故事线和演讲节奏
        ↓
Phase 3  Slide Contract
为每页建立结构化页面契约
        ↓
Phase 4  Visual System
建立颜色、字体、网格、组件、图表和版式规则
        ↓
Phase 5  Vertical Slice
先制作 3 页代表性页面验证方向
        ↓
Phase 6  Build
从零生成或基于模板编辑可修改 PPTX
        ↓
Phase 7  Render QA
渲染、文字检查、边界检查、视觉检查
        ↓
Phase 8  Fix Loop
修复问题并重新渲染
        ↓
Phase 9  Ship
交付 PPTX、源代码、素材、证据表和 QA 报告
```

其中“纵向切片”建议选择：

1. 封面页
    
2. 最复杂的机制、架构或流程页
    
3. 数据结果或总结页
    

这三页通过后再批量生成剩余页面。

---

# 3. 必须加入的 Skill 包

## 3.1 P0：必须加入

|Skill|定位|主要产出|
|---|---|---|
|`ppt-workflow-orchestrator-zh`|PPT 总控路由和阶段门禁|完整任务路由、阶段状态、交付清单|
|`ppt-visual-system-zh`|视觉总监|`PRESENTATION_DESIGN.md`|
|`pptx-builder-zh`|从零创建 PPTX|可编辑 `.pptx`、源代码|
|`pptx-template-editor-zh`|分析并修改已有模板|模板映射表、修改后的 `.pptx`|
|`ppt-render-qa-zh`|渲染、视觉和几何质检|逐页图片、Montage、`qa-report.md`|

## 3.2 P1：强烈建议加入

|Skill|定位|适用场景|
|---|---|---|
|`ppt-data-storytelling-zh`|数据故事和图表选择|数学建模、科研、商业汇报|
|`ppt-speaker-delivery-zh`|演讲备注和时间控制|答辩、路演、课程讲解|
|`ppt-reference-library-zh`|优秀页面案例和视觉参考库|高审美、品牌发布、路演|
|`pptx-ci-zh`|PPT 自动化回归检查|长期维护、周报、批量报告|

## 3.3 现有 Skill 直接复用

不需要重新创建：

```text
info-evidence-chain-zh
plan-faithful-execution-zh
subagent-orchestration-zh
artifact-curator-zh
workflow-forge-zh
```

推荐调用关系：

```text
正式汇报
主：ppt-workflow-orchestrator-zh
辅：info-evidence-chain-zh
验收：ppt-render-qa-zh
```

```text
从已有模板修改
主：ppt-workflow-orchestrator-zh
辅：pptx-template-editor-zh
验收：ppt-render-qa-zh
```

```text
科研数据答辩
主：ppt-workflow-orchestrator-zh
辅：ppt-data-storytelling-zh
验收：ppt-render-qa-zh
```

---

# 4. 推荐目录结构

```text
skills/presentation/
├── ppt-workflow-orchestrator-zh/
│   ├── SKILL.md
│   ├── agents/
│   │   └── openai.yaml
│   ├── references/
│   │   ├── workflow-modes.md
│   │   ├── slide-contract-schema.md
│   │   ├── delivery-contract.md
│   │   └── source-map.md
│   └── assets/
│       └── project-brief-template.md
│
├── ppt-story-design-zh/
│   ├── SKILL.md
│   ├── references/
│   │   ├── narrative-archetypes.md
│   │   ├── claim-evidence-map.md
│   │   └── ppt-story-rules.md
│   └── assets/
│       └── slide-spec-template.json
│
├── ppt-visual-system-zh/
│   ├── SKILL.md
│   ├── references/
│   │   ├── design-system-contract.md
│   │   ├── layout-grammar.md
│   │   ├── typography-rules.md
│   │   ├── anti-ai-patterns.md
│   │   └── visual-qa-checklist.md
│   └── assets/
│       ├── presentation-design-template.md
│       └── visual-reference-index.md
│
├── pptx-builder-zh/
│   ├── SKILL.md
│   ├── references/
│   │   ├── pptxgenjs-guide.md
│   │   ├── component-contract.md
│   │   └── common-pitfalls.md
│   ├── scripts/
│   │   ├── init-deck.ts
│   │   ├── theme.ts
│   │   ├── components.ts
│   │   └── check-bounds.ts
│   └── assets/
│       └── starter/
│
├── pptx-template-editor-zh/
│   ├── SKILL.md
│   ├── references/
│   │   ├── template-analysis.md
│   │   ├── slide-mapping.md
│   │   └── xml-editing-risks.md
│   └── scripts/
│       ├── unpack.py
│       ├── pack.py
│       ├── inspect_template.py
│       └── clean_orphans.py
│
├── ppt-render-qa-zh/
│   ├── SKILL.md
│   ├── references/
│   │   ├── acceptance-checklist.md
│   │   └── qa-severity-levels.md
│   └── scripts/
│       ├── render_slides.py
│       ├── make_montage.py
│       ├── extract_text.py
│       ├── check_geometry.py
│       └── build_qa_report.py
│
└── ppt-data-storytelling-zh/
    ├── SKILL.md
    ├── references/
    │   ├── chart-selection.md
    │   ├── chart-styling.md
    │   └── data-integrity.md
    └── assets/
        └── chart-spec-template.json
```

---

# 5. 需要安装的工具包

## 5.1 核心生成工具

```bash
npm install pptxgenjs
```

PptxGenJS 能生成文本、形状、图片、表格、图表、SVG 和母版等原生 PowerPoint 对象，输出兼容 PowerPoint、Keynote、LibreOffice 和 Google Slides 导入的 OOXML 文件，适合作为从零创建 PPTX 的主引擎。

推荐附加：

```bash
npm install sharp react react-dom react-icons
```

用途：

- `sharp`：图片裁切、压缩、SVG 转 PNG
    
- `react-icons`：生成统一图标
    
- `react`、`react-dom`：将图标组件渲染为 SVG
    

Anthropic 的 PptxGenJS 实践也采用了这一图标处理链路。

## 5.2 PPT 内容检查

```bash
pip install "markitdown[pptx]"
pip install Pillow
pip install defusedxml
pip install python-pptx
```

用途：

- `markitdown[pptx]`：提取整套 PPT 文本
    
- `Pillow`：生成缩略图和 Montage
    
- `defusedxml`：安全解析 PPTX XML
    
- `python-pptx`：读取或保守修改已有 PPTX
    

## 5.3 渲染环境

Ubuntu/Debian：

```bash
sudo apt update
sudo apt install libreoffice poppler-utils
```

渲染链：

```bash
libreoffice --headless --convert-to pdf presentation.pptx
pdftoppm -jpeg -r 150 presentation.pdf slide
```

这也是当前公开 PPTX Skill 使用的主要视觉质检方式。

---

# 6. 外部 Skill 包如何处理

## 6.1 推荐重点参考：`anthropics/skills/skills/pptx`

该 Skill 已包含：

- PPTX 内容读取
    
- 缩略图生成
    
- 模板分析
    
- 解包和重新打包
    
- PptxGenJS 从零创建
    
- 视觉检查提示词
    
- LibreOffice 和 Poppler 渲染
    
- 必须执行至少一轮修复—复验
    

这套结构非常适合成为你仓库 PPT Skill 的技术参考。

但需要注意：

> 该仓库的 PPTX 文档 Skill 属于 source-available，而不是普通开源许可。

因此建议：

```text
学习结构和技术方案
重新编写中文 Skill
自行实现脚本
保留 upstream source-map
不要直接整包复制后重新分发
```

Anthropic 仓库明确说明其 PPTX、PDF、DOCX、XLSX 文档 Skill 是生产实现参考，但并非普通开源 Skill。

## 6.2 加入视觉示例，而不只有文字规则

前沿 Skill 正在从纯文本说明转向“文字规则 + 视觉示例 + 按需加载”。近期 VISUALSKILL 研究表明，在 GUI 和视觉任务中保留图像示例，比仅将视觉经验转写成文字更有帮助。

因此建议在 `ppt-reference-library-zh` 中保存：

```text
references/
├── title-slide-good.png
├── title-slide-bad.png
├── data-slide-good.png
├── data-slide-bad.png
├── process-slide-good.png
├── process-slide-bad.png
└── visual-reference-index.md
```

不要一次向上下文加载全部图片，而是在对应页面类型出现时按需读取。

---

# 7. 新版 Slide Contract

建议将现有 Markdown 表格升级为结构化 JSON：

```json
{
  "slide_id": "S06",
  "section": "核心方案",
  "purpose": "解释系统如何完成从输入到结果的闭环",
  "audience_takeaway": "方案不是单次生成，而是可验证的执行闭环",
  "claim": "浏览器验证和反馈修复是可靠交付的必要组成部分",
  "evidence_refs": [
    "SRC-003",
    "SRC-007"
  ],
  "visual_type": "circular_process",
  "layout_family": "center-diagram-with-side-annotations",
  "dominant_asset": "agent-loop.svg",
  "content_blocks": [
    {
      "type": "process_node",
      "content": "PLAN"
    },
    {
      "type": "process_node",
      "content": "BUILD"
    },
    {
      "type": "process_node",
      "content": "VERIFY"
    },
    {
      "type": "process_node",
      "content": "FIX"
    }
  ],
  "text_budget": {
    "title": 18,
    "body": 55,
    "footer": 20
  },
  "source_footer": [
    "SRC-003"
  ],
  "speaker_notes": "先说明传统的一次生成方式，再讲闭环差异。",
  "qa_checks": [
    "流程方向清晰",
    "节点不超过5个",
    "文字无溢出",
    "引用可追溯"
  ]
}
```

---

# 8. 用于改造仓库的完整提示词

下面这份用于直接交给 Codex，让其在 `zbh-s-skills` 中实施改造。

你是一名 Agent Skills 架构师、PPT 内容策划、演示视觉设计师、PPTX 工程师和质量保证工程师。

目标：在当前仓库 `Hb-zzz-momo/zbh-s-skills` 中，将现有的 `ppt-story-design-zh` 从单一 PPT 叙事规划 Skill，升级为覆盖“证据、叙事、设计、构建、渲染、修复和交付”的完整 PPT 制作 Skill 工作流。

## 一、执行原则

1. 首先读取并理解以下现有文件，不得直接开始创建文件：
    
    - `skills/presentation/ppt-story-design-zh/SKILL.md`
        
    - `skills/presentation/ppt-story-design-zh/references/ppt-story-rules.md`
        
    - `skills/presentation/ppt-story-design-zh/assets/ppt-outline-template.md`
        
    - `skills/presentation/ppt-story-design-zh/agents/openai.yaml`
        
    - `skills/SKILL_ROUTING.zh-CN.md`
        
    - `skills/guardrail/skill-router-zh/SKILL.md`
        
    - `skills/engineering/web-design-workflow-zh/SKILL.md`
        
    - `skills/agent-skills-ao/USAGE.zh-CN.md`
        
    - 仓库根目录 `README.md`
        
2. 保留现有仓库的两层路由结构和最小加载原则：
    
    - 每个阶段仅允许 1 个主 Skill。
        
    - 最多追加 2 个辅助 Skill。
        
    - 不允许一次性加载全部 PPT Skills。
        
3. 复用现有工程生命周期：
    
    - Define
        
    - Plan
        
    - Build
        
    - Verify
        
    - Review
        
    - Ship
        
4. 不得删除或破坏现有 Skill。
    
5. 不得直接复制受限制许可的外部 Skill 源码。
    
6. 所有外部参考必须记录到 `references/source-map.md`，包含：
    
    - 仓库或文档名称
        
    - 上游路径
        
    - 参考日期
        
    - 参考内容
        
    - 许可状态
        
    - 本地采用方式
        

## 二、目标工作流

构建以下 PPT 制作闭环：

```text
材料读取
→ 任务分支判断
→ 证据链
→ 叙事结构
→ Slide Contract
→ PRESENTATION_DESIGN.md
→ 三页纵向切片
→ PPTX 构建或模板编辑
→ 全量渲染
→ 内容与视觉 QA
→ 修复和重新渲染
→ 最终交付
```

## 三、任务分支

总控 Skill 必须区分：

### A. 仅规划

用户只需要：

- PPT 大纲
    
- 页面结构
    
- 故事线
    
- 演讲顺序
    

只调用：

```text
ppt-story-design-zh
info-evidence-chain-zh
```

### B. 从零创建 PPTX

用户没有可复用模板，需要生成原生可编辑 PPTX。

调用：

```text
ppt-story-design-zh
ppt-visual-system-zh
pptx-builder-zh
ppt-render-qa-zh
```

构建引擎优先使用 PptxGenJS。

### C. 基于模板创建

用户提供现有 `.pptx` 模板。

调用：

```text
ppt-story-design-zh
pptx-template-editor-zh
ppt-render-qa-zh
```

流程必须先分析模板缩略图和文本，再进行页面映射。不得先改模板再理解其结构。

### D. 修改已有 PPTX

用户要求增删、替换或调整已有幻灯片。

必须：

1. 先备份原文件。
    
2. 分析页面结构、主题、母版和字体。
    
3. 保守修改。
    
4. 生成新文件，不覆盖原文件。
    
5. 渲染受影响页面并回归检查。
    

### E. 数据或科研型 PPT

追加：

```text
ppt-data-storytelling-zh
```

确保：

- 图表类型正确。
    
- 指标方向正确。
    
- 数据来源可追溯。
    
- 不使用误导性坐标轴。
    
- 统计结论不超出数据支持范围。
    

## 四、需要创建的 Skills

### 1. `ppt-workflow-orchestrator-zh`

职责：

- 任务分支判断
    
- 阶段路由
    
- 输入材料检查
    
- 阶段 Gate
    
- 最终交付检查
    

该 Skill 只负责总控和路由，不承担具体页面设计或代码实现。

### 2. `ppt-visual-system-zh`

职责：

- 创建 `PRESENTATION_DESIGN.md`
    
- 定义颜色、字体、网格、间距、圆角、图标和图表规范
    
- 定义视觉主题和唯一视觉母题
    
- 定义页面布局家族
    
- 进行 Taste Gate 审美检查
    
- 防止默认 AI 风格
    

必须建立以下可量化变量：

```text
LAYOUT_VARIANCE: 1-10
VISUAL_DENSITY: 1-10
COLOR_INTENSITY: 1-10
IMAGE_DOMINANCE: 1-10
MOTION_INTENSITY: 1-10
```

### 3. `pptx-builder-zh`

职责：

- 使用 PptxGenJS 从零创建 PPTX
    
- 生成原生可编辑对象
    
- 建立 theme、component、layout 和 slide 模块
    
- 支持文本、形状、图片、SVG、表格和图表
    
- 生成演讲者备注
    
- 输出源代码和 PPTX
    

禁止：

- 将整页截图作为主要内容
    
- 将复杂文本直接烘焙进图片
    
- 每页重复标题加项目符号
    
- 随机硬编码颜色和间距
    

### 4. `pptx-template-editor-zh`

职责：

- 分析已有模板
    
- 生成模板布局清单
    
- 建立内容到模板页面的映射
    
- 处理 PPTX 解包、修改、清理和重新打包
    
- 删除多余占位元素和孤立资源
    
- 保留原有母版、主题、字体和动画能力
    

### 5. `ppt-render-qa-zh`

职责：

- PPTX 转 PDF
    
- PDF 转逐页图片
    
- 生成缩略图 Montage
    
- 提取 PPT 全文
    
- 检查文字溢出、元素越界、遮挡和错位
    
- 检查图片失真、低分辨率和裁切
    
- 检查跨页一致性和信息节奏
    
- 生成 `qa-report.md`
    
- 执行修复—复验循环
    

必须规定：

```text
首次生成结果不能直接声明完成。
至少执行一次完整的检查、问题记录、修复和重新验证。
```

### 6. `ppt-data-storytelling-zh`

职责：

- 根据问题选择图表
    
- 设计结论先行的数据页面
    
- 建立数据源和图表映射
    
- 检查图表误导风险
    
- 输出图表规格 JSON
    

## 五、必须升级现有 `ppt-story-design-zh`

在保留现有能力的基础上增加：

1. PPT 类型判断：
    
    - 课程汇报
        
    - 学术答辩
        
    - 创新创业路演
        
    - 商业提案
        
    - 产品发布
        
    - 技术方案
        
    - 数据报告
        
2. 明确听众最终决策：
    
    - 理解
        
    - 相信
        
    - 选择
        
    - 投资
        
    - 批准
        
    - 采用
        
    - 继续讨论
        
3. 输出 Claim-Evidence Map：
    
    - 关键主张
        
    - 支撑证据
        
    - 来源
        
    - 证据强度
        
    - 缺失信息
        
4. 输出结构化 `slide-spec.json`，每页包含：
    
    - slide_id
        
    - section
        
    - purpose
        
    - audience_takeaway
        
    - claim
        
    - evidence_refs
        
    - visual_type
        
    - layout_family
        
    - dominant_asset
        
    - content_blocks
        
    - text_budget
        
    - source_footer
        
    - speaker_notes
        
    - qa_checks
        
5. 增加演讲时间预算：
    
    - 总时长
        
    - 每章时长
        
    - 每页建议时长
        
    - 可删减页面
        
    - 超时应急版本
        

## 六、视觉要求

创建 `references/anti-ai-patterns.md`，明确禁止：

- 连续多页使用同一种卡片网格
    
- 默认紫蓝渐变
    
- 无意义的发光边框
    
- 固定三列卡片
    
- 每页标题下添加装饰横线
    
- 大量居中的正文
    
- 没有信息意义的几何装饰
    
- 无来源的科技背景图
    
- 将图标当作主要信息
    
- 页面之间没有视觉节奏变化
    

建立以下原则：

1. 每页只表达一个核心结论。
    
2. 标题应直接表达结论，而不是只写章节名称。
    
3. 每页至少有一个有信息意义的视觉对象。
    
4. 同一套 PPT 只保留一个主要视觉母题。
    
5. 页面布局需要变化，但设计令牌保持统一。
    
6. 视觉复杂度必须服务于信息，而不是装饰。
    

## 七、三页纵向切片

批量生成整套 PPT 前，先制作：

1. 封面页
    
2. 最复杂的流程、架构或机制页
    
3. 数据结果或总结页
    

检查：

- 整体风格是否匹配主题
    
- 字体和字号是否合理
    
- 视觉母题是否成立
    
- 图表和图形是否清晰
    
- 信息密度是否合适
    
- 是否存在明显 AI 模板感
    

方向错误时只返工这三页，不直接生成全套。

## 八、工具和脚本

建议实现以下脚本：

```text
render_slides.py
make_montage.py
extract_text.py
check_geometry.py
check_image_resolution.py
build_qa_report.py
unpack.py
pack.py
clean_orphans.py
```

核心依赖：

```text
pptxgenjs
sharp
react-icons
markitdown[pptx]
Pillow
defusedxml
python-pptx
LibreOffice
Poppler
```

所有依赖必须：

- 写入安装文档
    
- 检查是否已安装
    
- 缺失时给出明确命令
    
- 不得假设运行环境已经具备
    

## 九、路由文件修改

修改：

```text
skills/SKILL_ROUTING.zh-CN.md
skills/guardrail/skill-router-zh/SKILL.md
```

将 PPT 默认主入口改为：

```text
ppt-workflow-orchestrator-zh
```

推荐路由说明：

```text
汇报 / PPT
主 Skill：ppt-workflow-orchestrator-zh

仅规划：
ppt-story-design-zh + info-evidence-chain-zh

从零生成：
pptx-builder-zh + ppt-render-qa-zh

模板编辑：
pptx-template-editor-zh + ppt-render-qa-zh

数据型汇报：
ppt-data-storytelling-zh + ppt-render-qa-zh
```

## 十、验收要求

完成后必须检查：

1. 每个新 Skill 均包含合法 YAML Frontmatter。
    
2. `name` 唯一且使用小写连字符。
    
3. `description` 包含明确 Use when 触发条件。
    
4. 每个 Skill 职责单一，不与其他 Skill 大量重复。
    
5. 总控 Skill 不承担具体实现。
    
6. 所有引用文件路径存在。
    
7. 所有脚本具有帮助说明和错误处理。
    
8. 路由文档已更新。
    
9. README 已通过仓库既有脚本重新生成。
    
10. 创建一个最小示例项目，生成 8～12 页测试 PPT。
    
11. 测试 PPT 必须经过渲染、Montage、QA 和至少一次修复。
    
12. 输出最终变更清单、验证命令、验证结果和剩余风险。
    

## 十一、最终交付

输出：

```text
新增 Skill 列表
修改文件列表
完整目录树
各 Skill 职责说明
安装依赖说明
路由说明
示例调用方式
测试 PPT 路径
渲染图片路径
Montage 路径
qa-report.md 路径
未完成项和风险
```

不要只创建空目录或概念文档。必须保证至少一条“从输入材料到生成并验收 PPTX”的链路真实可运行。

---

# 9. 优化后日常制作 PPT 的调用提示词

使用当前仓库的 PPT Skills 制作一份完整演示文稿。

## 1. 基本信息

- 主题：`{PPT主题}`
    
- 使用场景：`{课程汇报/学术答辩/创新创业路演/商业提案/产品发布/技术方案}`
    
- 目标听众：`{听众}`
    
- 期望听众最终行动：`{理解/相信/选择/批准/投资/采用}`
    
- 演讲时长：`{分钟}`
    
- 目标页数：`{页数}`
    
- 输出语言：`{中文/英文}`
    
- 页面比例：16:9
    
- 输出格式：可编辑 PPTX
    
- 视觉方向：`{科技/正式/极简/苹果发布会/杂志编辑/学术}`
    
- 品牌颜色：`{颜色或无}`
    
- 参考文件：`{路径或无}`
    
- 数据材料：`{路径或无}`
    
- PPT 模板：`{路径或无}`
    

## 2. Skill 路由

主 Skill：

```text
ppt-workflow-orchestrator-zh
```

按任务阶段动态选择辅助 Skill，不得一次加载全部：

```text
证据阶段：info-evidence-chain-zh
叙事阶段：ppt-story-design-zh
视觉阶段：ppt-visual-system-zh
从零构建：pptx-builder-zh
模板修改：pptx-template-editor-zh
数据页面：ppt-data-storytelling-zh
最终验收：ppt-render-qa-zh
```

## 3. 工作流程

### Phase 0：材料读取

首先读取所有用户材料、模板、品牌规范、数据文件和已有图片。

输出：

```text
brief.md
material-inventory.md
missing-information.md
```

不得在未读取材料前直接生成 PPT。

### Phase 1：证据链

建立：

```text
sources.md
claim-evidence-map.md
```

所有事实、数字、政策、案例和引用必须可追溯。

没有来源的内容必须标记为：

```text
待核验
推断
建议
示例数据
```

不得编造事实、数据、专家观点和合作成果。

### Phase 2：叙事设计

输出：

```text
storyline.md
```

必须包含：

- 一句话核心主张
    
- 听众当前认知
    
- 希望听众形成的新认知
    
- 核心矛盾
    
- 叙事主线
    
- 章节结构
    
- 每章作用
    
- 演讲时间分配
    
- 可删除页面
    
- 超时应急版本
    

### Phase 3：逐页契约

输出：

```text
slide-spec.json
```

每页必须包含：

```text
slide_id
section
purpose
audience_takeaway
claim
evidence_refs
visual_type
layout_family
dominant_asset
content_blocks
text_budget
source_footer
speaker_notes
qa_checks
```

一页只允许一个主要结论。

### Phase 4：视觉系统

输出：

```text
PRESENTATION_DESIGN.md
```

至少定义：

- Design Read
    
- 颜色令牌
    
- 字体层级
    
- 页面网格和安全边距
    
- 标题、正文、注释字号
    
- 页面布局家族
    
- 图片风格
    
- 图标风格
    
- 图表风格
    
- 圆角、阴影和描边
    
- 唯一视觉母题
    
- 页面节奏
    
- 禁止使用的 AI 模板模式
    

不要只使用“高级、科技、简洁”等抽象词，必须转换成可执行参数。

### Phase 5：三页纵向切片

先生成：

1. 封面
    
2. 最复杂的机制或流程页
    
3. 数据结果或总结页
    

渲染并检查后，再生成剩余页面。

### Phase 6：PPTX 构建

从零创建时使用 PptxGenJS。

要求：

- 所有文字、形状、图表尽可能为原生可编辑对象。
    
- 不得将整页截图作为幻灯片。
    
- 照片和插画允许使用图片。
    
- 图表必须来自真实数据。
    
- 颜色、字体、间距全部来自 `PRESENTATION_DESIGN.md`。
    
- 公共组件必须复用。
    
- 页面布局应有变化，但视觉令牌保持统一。
    
- 不得连续多页使用标题加项目符号。
    
- 不得重复使用无意义的三列卡片。
    

### Phase 7：内容检查

执行：

```bash
python -m markitdown presentation.pptx
```

检查：

- 页面顺序
    
- 内容缺失
    
- 错别字
    
- 占位文本
    
- 重复内容
    
- 引用遗漏
    
- 数据与正文不一致
    

### Phase 8：视觉渲染

执行：

```text
PPTX → PDF → 逐页图片 → Montage
```

检查：

- 元素越界
    
- 文字被裁切
    
- 图片拉伸
    
- 图表不可读
    
- 字体替换
    
- 元素遮挡
    
- 间距不一致
    
- 页边距过小
    
- 对比度不足
    
- 引用与正文碰撞
    
- 连续页面过于单调
    
- 信息密度突然变化
    

### Phase 9：修复循环

首次渲染不得直接宣布完成。

必须：

```text
记录问题
→ 修复问题
→ 重新生成
→ 重新渲染
→ 重新检查
```

至少完成一轮修复和复验。

### Phase 10：最终交付

交付：

```text
presentation.pptx
完整源代码
brief.md
sources.md
claim-evidence-map.md
storyline.md
slide-spec.json
PRESENTATION_DESIGN.md
assets/
逐页渲染图片
Montage
qa-report.md
```

同时说明：

- 使用了哪些 Skills
    
- 使用了哪条任务分支
    
- 执行过哪些命令
    
- 修复了哪些问题
    
- 哪些内容仍待用户确认
    
- 最终文件路径
    

建议先执行仓库改造提示词，再使用日常提示词制作一套 8～12 页示例 Deck，将其作为后续 Skill 更新时的固定回归样例。

---

