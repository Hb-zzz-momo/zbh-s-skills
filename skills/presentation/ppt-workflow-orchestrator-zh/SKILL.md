---
name: ppt-workflow-orchestrator-zh
description: "PPT 制作总控与阶段门禁技能：把材料、证据、叙事、逐页契约、视觉系统、PPTX 构建或模板编辑、渲染质检、修复复验和交付串成闭环。Use when: 做完整PPT、生成可编辑PPTX、基于模板做PPT、修改已有PPTX、PPT渲染验收、答辩或路演全流程。只需要单页视觉规则时使用 ppt-visual-system-zh，只需要故事线时使用 ppt-story-design-zh。"
---

# PPT 制作总控
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 职责边界

只做任务分支、阶段路由、输入检查、Gate 和交付检查。不要在本 Skill 内代替叙事、视觉、构建、模板编辑或 QA Skill 完成专业实现。

始终遵守：每个阶段只设 1 个主 Skill，最多追加 2 个辅助 Skill；阶段结束后卸载不再需要的上下文，不得一次加载全部 PPT Skills。

## 硬门槛

在开始 Build 前记录：

```text
触发门槛：任务包含 PPTX 构建、模板修改或正式交付。
前置证据：已读取材料、模板、品牌规范、数据和交付要求。
禁止越界：不得编造数据、覆盖原稿、跳过纵向切片或首次渲染后直接交付。
判定结果：PASS / CAUTION / BLOCK。
下一步动作：放行、补材料、降级为仅规划或暂停询问。
```

只有输入足以支持当前阶段时判定 `PASS`。缺品牌素材但可使用用户认可的中性系统时为 `CAUTION`；缺主题、交付格式、关键数据或模板文件时为 `BLOCK`。

正式任务使用 `scripts/ppt_workflow.py` 持久化阶段状态；不得只在对话中口头记录。先运行 `scripts/check_dependencies.py` 和 `scripts/validate_contract.py`。状态机强制逐阶段推进，三页切片未结构化批准时不能进入全量构建，最终 QA 报告未明确 `PASS` 时不能进入 Ship。

## Phase 0：Intake 与分支

1. 先读取题目、全部参考材料、数据、图片、模板、品牌规范和交付要求。
2. 使用 `assets/project-brief-template.md` 产出 `brief.md`、`material-inventory.md` 和 `missing-information.md`。
3. 按 `references/workflow-modes.md` 选择且只选择一个主分支：
   - A 仅规划。
   - B 从零创建 PPTX。
   - C 基于模板创建。
   - D 修改已有 PPTX。
   - E 数据或科研增强，叠加在 B/C/D 上。
4. 将分支、辅助 Skill、输出目录和 Gate 状态写入阶段记录。

## Phase 1–4：计划契约

按顺序推进，不得跳级：

| 阶段 | 主 Skill | 可选辅助 | 必须产出 | Gate |
|---|---|---|---|---|
| Evidence | `info-evidence-chain-zh` | 无 | `sources.md`, `claim-evidence-map.md` | 主张可追溯；缺口有标签 |
| Narrative | `ppt-story-design-zh` | `info-evidence-chain-zh` | `storyline.md`, `slide-spec.json` | 一页一个结论；时间预算完整 |
| Visual System | `ppt-visual-system-zh` | 无 | `PRESENTATION_DESIGN.md` | 令牌可执行；Taste Gate 通过 |

<!-- contextual-reference-router:gate:v1:start -->
### 条件 Reference Route Gate

该 Gate 是阶段内检查点，不新增 `ppt_workflow.py` 状态：

- 新建或重设计 PPT 默认调用 `contextual-reference-router`；只有用户提供完整模板并要求严格局部修改、或明确禁止外部参考时跳过。需要行业 Deck、外部视觉案例或用户要求“参考优秀 PPT”时同样必须调用。
- 结构与叙事参考：Evidence 通过后、Narrative 前形成 `reference-brief.md`。
- 纯视觉参考：Narrative 通过后、Visual System 前形成或补充 `reference-brief.md`。
- 事实来源仍归 `info-evidence-chain-zh`；外部设计案例不能作为数字、政策、合作或研究 claim 的证据。
- `contextual-reference-router` 负责动态外部案例；`ppt-reference-library-zh` 负责本地成对优秀/反例与页面级审美门。默认按缺口选择一个，只有维度互补时才同时加载。
- Reference Brief 必须记录具体多页案例、采用/不采用规律、页面转译、访问与许可限制；`BLOCK` 时不得进入依赖该参考的 Narrative 或 Visual System。
- 完成后退出参考 Skill，不改变每阶段 1 个主 Skill、最多 2 个辅助 Skill 的预算。
<!-- contextual-reference-router:gate:v1:end -->

事实、推断、建议和示例数据必须分开标注。未经证据支持的数字、政策、案例、专家观点和合作成果不得进入正式幻灯片。

## Phase 5：风险驱动纵向切片

基础切片先构建并渲染：封面页；最复杂的流程、架构或机制页；数据结果页，无数据时使用总结页。

三页只是最低数量，不是固定上限。出现以下任一高风险家族时必须追加对应代表页：

- 多个不同拓扑的箭头页：分别覆盖闭环、跨行阶梯/流水线、径向迁移，不得只抽其中一页。
- 卡片、表格或矩阵存在高文本密度：追加全文字最多、最后一段最靠近容器底边的页面。
- 同一 Deck 使用两种以上卡片家族：每种至少检查一个最密实例。

切片记录必须列出 `risk_family -> slide_id` 映射；缺少箭头语义页或文本容器页时不得进入全量构建。

检查主题匹配、字体、视觉母题、信息密度、图表清晰度和 AI 模板感。触发 Reference Route Gate 时，还要检查参考规律是否真实落实、是否直接复制单个案例。方向错误时只返工三页，不得批量生成全套。

## Phase 6：Build

- 从零创建：以 `pptx-builder-zh` 为主，生成原生可编辑对象、源代码和新 PPTX。
- 基于模板：以 `pptx-template-editor-zh` 为主，先分析缩略图、文本、主题和母版，再建立页面映射。
- 修改已有：先复制原文件，保守修改并输出新文件；不得覆盖原稿。
- 数据增强：仅在处理数据页时追加 `ppt-data-storytelling-zh`，完成后退出该辅助 Skill。

## Phase 7–8：Render QA 与 Fix Loop

切换 `ppt-render-qa-zh` 为主 Skill：

```text
PPTX → PDF → 逐页图片 → Montage
     → 文本/几何/图片/视觉检查
     → 问题记录 → 修复 → 重新构建
     → 重新渲染 → 重新检查
```

首次生成结果不能声明完成。至少执行一轮完整的检查、问题记录、修复和复验；受影响页面与全局 Montage 都要复查。

## Phase 9：Ship

按 `references/delivery-contract.md` 检查交付包。最低交付包括 PPTX 与源代码、材料/证据/叙事/设计契约、素材、逐页渲染图片、Montage、`qa-report.md` 和 `fix-log.md`；触发参考路由时追加 `reference-brief.md` 与参考落实状态。

最终说明任务分支、使用过的 Skills、实际命令、修复项、待确认项和绝对路径。

最后运行 `scripts/validate_delivery.py` 生成带 SHA-256 的交付清单。包含演讲任务时追加 `ppt-speaker-delivery-zh`；需要审美参考时按页面类型加载 `ppt-reference-library-zh`；长期维护或批量生成时用 `pptx-ci-zh` 建立同引擎基线回归。三者均按阶段加载，不与全部 PPT Skills 同时进入上下文。

```powershell
python scripts/ppt_workflow.py init --project output --mode from-scratch
python scripts/ppt_workflow.py advance --project output --to evidence
python scripts/validate_delivery.py output --output output/delivery-manifest.json
```

## 资源导航

- 分支与阶段路由：`references/workflow-modes.md`
- Slide Contract：`references/slide-contract-schema.md`
- 交付契约：`references/delivery-contract.md`
- 外部来源与许可：`references/source-map.md`
- 项目简报模板：`assets/project-brief-template.md`
