---
name: ppt-speaker-delivery-zh
description: "PPT 演讲备注与时间控制技能：把逐页 speaker_notes 转为可执行讲稿，按目标时长分配页面时间，检查无备注页、超时页、节奏突变和应急删页，并输出 timing-report.json/brief.md。Use when: 答辩、路演、课程汇报、演讲备注、演讲时长、逐页讲稿、超时应急版。"
---

# PPT 演讲交付
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 工作流

1. 读取 `slide-spec.json` 的 `speaker_notes`、章节、页面目的和目标时长。
2. 运行 `scripts/validate_delivery.py`，生成逐页时间、总时长、无备注页和节奏异常报告。
3. 对无备注页或超时页返回 `BLOCK`；调整备注后重新运行。
4. 把最终时间写入演讲者备注或交付 `speaker-timing.json`，并准备可删页和超时应急顺序。

## 硬门禁

- 不得用页面正文冒充演讲备注。
- 每页必须有目的明确的备注；数据页必须说明口径与结论，不能只念数字。
- 总预算超过目标时长 5% 判为 `BLOCK`；单页时间突变超过 2.5 倍判为 `CAUTION`。
- 最终交付必须包含逐页时间与总时间验证结果。
