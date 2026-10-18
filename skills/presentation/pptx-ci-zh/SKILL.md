---
name: pptx-ci-zh
description: "PPTX 自动化回归技能：在 CI 或本地执行契约校验、构建、渲染、内容/几何/图片/图表检查和基线视觉差异比较，输出机器可读 ci-report.json；适合周报、批量报告和长期维护。Use when: PPT CI、PPT回归、批量生成、渲染基线、视觉diff、GitHub Actions。"
---

# PPTX CI
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

1. 使用 `scripts/compare_render.py` 对同页 PNG 做像素差异评估。
2. 使用 `scripts/run_ci.py --checks ...` 汇总各阶段 JSON；任一 `BLOCK/FAIL` 或 ERROR/BLOCKER 使流水线失败。
3. 将 `assets/github-actions-pptx.yml` 复制到项目工作流后，按项目路径替换命令。
4. 基线只能在人工确认新渲染正确后更新，不能为了让 CI 变绿自动覆盖。
