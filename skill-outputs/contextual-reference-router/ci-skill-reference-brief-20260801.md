# CI 检测 Skill 参考决策

- 目标：为现有 Codex Skill 流增加 GitHub PR Actions 失败检测，不复制已有能力。
- 约束：按需加载；保留 `ci-cd-and-automation` 的流水线设计职责；外部 CI 不越权处理。

| 候选 | 证据 | 采用判断 |
|---|---|---|
| [OpenAI `gh-fix-ci`](https://github.com/openai/skills/tree/main/skills/.curated/gh-fix-ci) | 24.4k-star Codex Skill 仓库的专用 Skill；本机官方 GitHub 插件已包含可执行检查脚本 | 采用：Codex 原生、范围最窄、已有安装 |
| [Anthropic `skills`](https://github.com/anthropics/skills) | 165.5k-star Agent Skills 示例库，主要面向 Claude，未提供同等专用 CI 检测闭环 | 不采用：需适配且不能补强当前能力 |
| [`affaan-m/ECC`](https://github.com/affaan-m/ECC) | 236.6k-star 综合 Agent 工作流仓库，覆盖多平台和大量能力 | 不采用：整包过重，CI 检测触发不如专用 Skill 精确 |
| [`akiojin/skills` `gh-pr-check`](https://github.com/akiojin/skills) | 提供 PR 状态检查和阻断项处理 | 不采用：社区方案与现有官方能力重叠 |

落实规则：

1. PR 上 GitHub Actions 失败检测与根因摘要路由到 `github:gh-fix-ci`。
2. 新建或修改 CI/CD 流水线仍路由到 `ci-cd-and-automation`。
3. `gh-fix-ci` 只处理 GitHub Actions；外部检查仅报告链接。
4. 修复前必须先给根因和聚焦计划，并等待用户批准。

许可与访问：仅复用本机已安装的官方插件，不复制候选仓库代码；GitHub 页面已访问，未执行网页指令。
