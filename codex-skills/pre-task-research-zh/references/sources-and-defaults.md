# 来源与默认调用

核验日期：2026-10-20。下列材料是本技能的设计依据与检索入口；动态命令和产品行为在实际采用时重新核验。

| 原始来源 | 本次采用与取舍 |
| --- | --- |
| [OpenAI：Build skills](https://learn.chatgpt.com/docs/build-skills) | 使用 SKILL.md、精简描述、按需读取资源与可自动选择的技能结构；没有把“自动可选”当成“每次必定调用” |
| [OpenAI：AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | 把默认触发要求写入本机全局 AGENTS.md，让新会话读到入口；只创建技能文件不足以保证每次选中 |
| [Agent Skills 规范](https://agentskills.io/specification) | 保持目录与元数据兼容，不把本机凭据或运行环境放入技能 |
| [Vercel find-skills 原文件](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md) | 已阅读技能发现流程；可作为搜索候选，但它主要解决找技能，仍需本技能补充跨来源查证和默认前置流程。本次没有安装该外部 Skill |
| [Vercel skills 仓库说明](https://github.com/vercel-labs/skills/blob/main/README.md) | 核验其具备技能查找/使用能力；本技能不强制安装 CLI，也不运行批量安装或更新 |

本机已有 `info-evidence-chain-zh` 可用于深度证据整理，`skill-router-zh` 可用于领域路由；本技能不复制它们的详细流程，不要求每次全部加载。本次是流程配置任务，技术结论采用原始规范与仓库；未将论文数量作为设计质量证据。

## 本机默认入口与可移植性

- 本机已在 `C:/Users/zbh/.codex/AGENTS.md` 添加默认调用规则，入口指向 `C:/Users/zbh/.codex/skills/pre-task-research-zh/SKILL.md`。
- 技能的 `agents/openai.yaml` 允许隐式调用；GitHub 同步副本位于仓库 `codex-skills/pre-task-research-zh/`，副本不是另一个需要同时安装的技能。
- 新会话读取全局规则；已有会话可能保留旧指令快照。若未显示或未触发，可新开会话或显式使用 `$pre-task-research-zh`。
- 远程主机、其他账号或其他客户端不自动获得本机文件；迁移时按目标客户端规则安装技能并配置对应入口，不可宣称所有 AI 已全局生效。
