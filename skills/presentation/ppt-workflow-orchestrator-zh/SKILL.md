---
name: ppt-workflow-orchestrator-zh
description: "PPT 制作总控与阶段门禁技能：把材料、证据、叙事、逐页契约、视觉系统、PPTX 构建或模板编辑、渲染质检、修复复验和交付串成闭环。Use when: 做完整PPT、生成可编辑PPTX、基于模板做PPT、修改已有PPTX、PPT渲染验收、答辩或路演全流程。只需要单页视觉规则时使用 ppt-visual-system-zh，只需要故事线时使用 ppt-story-design-zh。"
---

# PPT 制作总控

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

事实、推断、建议和示例数据必须分开标注。未经证据支持的数字、政策、案例、专家观点和合作成果不得进入正式幻灯片。

## Phase 5：三页纵向切片

先构建并渲染以下代表页：封面页；最复杂的流程、架构或机制页；数据结果页，无数据时使用总结页。

检查主题匹配、字体、视觉母题、信息密度、图表清晰度和 AI 模板感。方向错误时只返工三页，不得批量生成全套。

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

按 `references/delivery-contract.md` 检查交付包。最低交付包括 PPTX 与源代码、材料/证据/叙事/设计契约、素材、逐页渲染图片、Montage、`qa-report.md` 和 `fix-log.md`。

最终说明任务分支、使用过的 Skills、实际命令、修复项、待确认项和绝对路径。

## 资源导航

- 分支与阶段路由：`references/workflow-modes.md`
- Slide Contract：`references/slide-contract-schema.md`
- 交付契约：`references/delivery-contract.md`
- 外部来源与许可：`references/source-map.md`
- 项目简报模板：`assets/project-brief-template.md`

