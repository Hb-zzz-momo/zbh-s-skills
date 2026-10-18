---
name: ppt-story-design-zh
description: "PPT 叙事与逐页契约技能：面向课程汇报、学术答辩、创新创业路演、商业提案、产品发布、技术方案和数据报告，确定听众决策、核心主张、证据链、故事线、时间预算并输出结构化 slide-spec.json。Use when: PPT大纲、页面结构、故事线、演讲顺序、Claim-Evidence Map、逐页契约、答辩叙事、路演结构。需要生成PPTX时由 ppt-workflow-orchestrator-zh 路由后续构建。"
---

# PPT 叙事与逐页契约
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 目标

先定清“讲什么、为什么可信、希望听众做什么、每页承担什么任务”，再把结果固化为可验证的逐页契约。不要在本 Skill 中生成 PPTX 或替代视觉系统。

## Step 1：判定类型与决策

1. 从课程汇报、学术答辩、创新创业路演、商业提案、产品发布、技术方案、数据报告中选择最接近的一类。
2. 明确听众与其当前认知。
3. 从理解、相信、选择、投资、批准、采用、继续讨论中选择期望的最终决策。
4. 写出一句话核心主张与核心矛盾。

按类型选择叙事骨架时读取 `references/narrative-archetypes.md`，不要机械套用固定章节。

## Step 2：建立 Claim-Evidence Map

为每个关键主张记录支撑证据、来源 ID、证据强度和缺失信息。使用 `references/claim-evidence-map.md`。

- 事实必须可追溯。
- 推断、建议和示例数据必须显式标记。
- 缺证据的主张可以保留在待办，不得包装为已证实结论。
- 竞品比较不得无证据点名攻击。

## Step 3：设计故事线

1. 描述听众当前认知与希望形成的新认知。
2. 用核心矛盾连接背景、问题、方案、证据、价值与行动。
3. 为每章写明作用、进入条件和离开时听众应形成的判断。
4. 页面顺序服务于决策，而不是材料原始顺序。

## Step 4：分配时间

输出总时长、每章时长、每页建议时长、可删减页面和超时应急版本。删减后仍须保留主张—证据—行动闭环。

## Step 5：建立逐页契约

使用 `assets/slide-spec-template.json` 输出 `slide-spec.json`。每页必须包含：

`slide_id`, `section`, `purpose`, `audience_takeaway`, `claim`, `evidence_refs`, `visual_type`, `layout_family`, `dominant_asset`, `content_blocks`, `text_budget`, `source_footer`, `speaker_notes`, `qa_checks`。

约束：

- 一页只表达一个主要结论。
- 标题表达结论，不只写章节名。
- 每页至少规划一个有信息意义的视觉对象。
- `evidence_refs` 与 `source_footer` 必须可解析。
- 页面契约描述信息与验收，不写死视觉坐标。

## 输出

- `storyline.md`
- `claim-evidence-map.md`
- `slide-spec.json`
- 演讲时间预算与超时应急版本

仅规划任务可同时提供 `assets/ppt-outline-template.md` 的人类可读摘要，但 JSON 是后续构建的权威输入。

## 资源

- 叙事类型：`references/narrative-archetypes.md`
- 主张证据映射：`references/claim-evidence-map.md`
- 叙事规则：`references/ppt-story-rules.md`
- 结构化契约：`assets/slide-spec-template.json`
- 旧版可读表格：`assets/ppt-outline-template.md`
