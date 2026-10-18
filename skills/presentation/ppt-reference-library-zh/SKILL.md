---
name: ppt-reference-library-zh
description: "PPT 视觉参考库技能：按封面、数据页、流程页按需加载成对的优秀/反例 PNG，解释层级、留白、图表、对齐、节奏和 AI 模板化问题，并把选用规则写入视觉系统。Use when: PPT视觉参考、好坏示例、审美门禁、封面设计、数据页设计、流程页设计。"
---

# PPT 视觉参考库
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

只加载与当前页面类型对应的一对示例；不要一次把全部图片加入上下文。先读 `references/visual-reference-index.md`，再查看所需 PNG。示例用于抽取布局与视觉原则，不得直接复制成最终页面背景。

需要更新参考图时运行 `scripts/generate_reference_images.py --output-dir references`，然后逐张人工确认。
