---
name: ppt-visual-system-zh
description: "PPT 视觉系统与审美门禁技能：把主题和品牌方向转成可执行的 PRESENTATION_DESIGN.md，定义颜色、字体、网格、间距、圆角、图标、图表、布局家族、唯一视觉母题与页面节奏。Use when: PPT视觉设计、演示设计规范、PRESENTATION_DESIGN.md、版式系统、三页纵向切片、Taste Gate、避免AI模板感。"
---

# PPT 视觉系统
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 目标与边界

创建可供构建代码直接消费的视觉契约。不要写空泛的“高级、科技、简洁”，不要生成 PPTX，不要替代叙事 Skill 决定主张。

## Step 1：Design Read

读取主题、听众、品牌规范、模板、素材和 `slide-spec.json`，写明：

- 场景与情绪。
- 内容的核心隐喻。
- 唯一视觉母题及其信息作用。
- 应延续和应避免的参考特征。

若用户提供模板，优先提取其主题令牌，不得另起一套冲突设计系统。

## Step 2：量化方向

为以下变量给出 1–10 的值与一句理由：

```text
LAYOUT_VARIANCE
VISUAL_DENSITY
COLOR_INTENSITY
IMAGE_DOMINANCE
MOTION_INTENSITY
```

## Step 3：建立设计令牌

使用 `assets/presentation-design-template.md` 定义：

- 16:9 页面尺寸、网格、安全边距和基准间距。
- 颜色角色与十六进制值；每个颜色说明用途和禁用场景。
- 中文/英文字体回退链、标题/正文/注释/数据字号。
- 圆角、描边、阴影、图标、图片和图表规则。
- 版式家族与页面节奏。

颜色、字体和间距必须用令牌名引用，禁止在页面代码中随机硬编码。

## Step 4：检查版式语法

按 `references/layout-grammar.md` 为每个 Slide Contract 选择版式家族。布局需要变化，但令牌保持统一；连续两页不应只有标题加项目符号。

## Step 5：Taste Gate

先检查 `references/anti-ai-patterns.md`，再用 `references/visual-qa-checklist.md` 审核三页纵向切片。

Gate 结果：

- `PASS`：视觉母题、层级、密度、对比与页面节奏均成立。
- `CAUTION`：可继续构建，但必须记录具体待修项。
- `BLOCK`：风格与主题不符、关键文字不可读或明显模板化；只返工三页。

## 输出

- `PRESENTATION_DESIGN.md`
- 三页纵向切片视觉检查记录
- 设计风险与字体替代说明

## 资源

- 契约要求：`references/design-system-contract.md`
- 布局语法：`references/layout-grammar.md`
- 字体规则：`references/typography-rules.md`
- AI 模板反模式：`references/anti-ai-patterns.md`
- 视觉 QA：`references/visual-qa-checklist.md`
