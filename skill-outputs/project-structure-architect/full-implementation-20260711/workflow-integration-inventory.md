# 跨工作流文件树门禁接入清单

## 接入结论

- 仓库内共有 61 个 `SKILL.md`。
- 57 个会创建、移动、初始化、归档或持续写入多文件产物的工作流，必须显式包含 `project-structure-architect` 门禁。
- 3 个纯审阅/版本工作流豁免：`code-review-and-quality`、`doubt-driven-development`、`git-workflow-and-versioning`。
- `project-structure-architect` 是门禁提供者，自身不递归接入。

## 统一契约

所有 57 个目标工作流均在首个 H1 后放置唯一一组
`project-structure-architect:gate:v1` marker。门禁要求：

1. 搭建或重组前读取 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 与现有文件树。
2. 运行中每次新增或移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物前，先按职责和所有者路由唯一位置。
3. 每个纵向切片结束检查结构漂移，最终运行结构审计；`BLOCK` 时停止结构性写入。
4. 仅当纯内容编辑且目标路径已由用户或既有规范唯一确定时，允许跳过重复调用。

## 全局接入点

- 根 `AGENTS.md`：全局项目结构门禁。
- `skills/guardrail/skill-router-zh/SKILL.md`：领域、风险、组合及生命周期路由。
- `skills/SKILL_ROUTING.zh-CN.md`：Step 1、Step 3、常用组合与默认守门规则。
- `skills/scripts/Update-SkillsReadme.ps1`：工程分组和生成式路由文案。
- `skills/README.md`：只由规范生成器重建，未手工维护。

## 自动验证

`tests/test_workflow_integration.py` 固化 required/exempt/provider 三类清单，并检查：

- 57 个 required skill 的开始/结束 marker 各且仅各一次；
- marker 位于首个 H1 后；
- 新增 workflow 不得处于未分类状态；
- 根门禁、两级路由、README 生成器及生成后的 README 同步存在；
- 所有 skill 均保持在 500 行以内。

最终命令、通过数与 fresh-agent 前向验证结果统一回填到 `validation-report.md`。
