# Subagent Role Catalog

## 来源摘要

| 来源 | 本地文件 | 可用价值 | 纳入策略 | 许可证状态 |
|---|---|---|---|---|
| awesome-codex-subagents | `C:\Users\zbh\.agents\awesome-codex-subagents-main.zip` | 167 个 Codex-native `.toml` 角色卡 | 只做精选角色库和提示参考，不批量安装 | MIT，Copyright (c) 2026 VoltAgent |
| Codex-Subagent-Orchestrator | `C:\Users\zbh\.agents\Codex-Subagent-Orchestrator-main.zip` | 父代理调度流程、run-kit、worker brief、acceptance 思路 | 本地原创改写，不直接复制完整 skill | 根目录未发现独立 LICENSE；vendored `agent-skills` 为 MIT |
| vendored agent-skills | 第二份 zip 的 `vendor/agent-skills/` | 工程 lifecycle discipline | 本地已有 `agent-skills-ao`，不重复导入 | MIT，Copyright (c) 2025 Addy Osmani |

## awesome-codex-subagents 实测结构

该 zip 是 TOML 角色卡库，不是本地 skill 包。

已观察到的实际字段：

```toml
name = "agent-name"
description = "when to use"
model = "..."
model_reasoning_effort = "..."
sandbox_mode = "read-only | workspace-write"
developer_instructions = """
...
"""
```

注意：README 示例里出现 `[instructions].text`，但实际 167 个 TOML 使用 `developer_instructions`。

## 第一批精选角色

### Meta / Orchestration

| 角色 | 默认用途 | 本地定位 |
|---|---|---|
| `context-manager` | 压缩项目上下文给下游代理 | explorer 参考 |
| `task-distributor` | 拆分独立任务和依赖图 | 父代理分工参考 |
| `workflow-orchestrator` | 设计阶段和等待点 | 父代理流程参考 |
| `multi-agent-coordinator` | 多代理计划、角色、依赖和集成 | 父代理编排参考 |
| `knowledge-synthesizer` | 汇总多个代理发现 | 回收结果参考 |

### Engineering

| 角色 | 默认用途 | 本地定位 |
|---|---|---|
| `code-mapper` | 映射代码路径、调用链和边界 | explorer |
| `code-reviewer` | 代码质量和风险审查 | late reviewer |
| `architect-reviewer` | 架构边界、耦合和长期维护审查 | late reviewer |
| `test-automator` | 测试设计和回归覆盖 | explorer 或 worker |
| `debugger` | 独立排查失败线程 | explorer |
| `performance-engineer` | 性能瓶颈和回归风险 | explorer 或 reviewer |
| `security-auditor` | 安全边界、输入、权限、密钥 | reviewer |

### Research

| 角色 | 默认用途 | 本地定位 |
|---|---|---|
| `scientific-literature-researcher` | 文献证据和质量加权综合 | explorer |
| `research-analyst` | 技术主题结构化调查 | explorer |
| `project-idea-validator` | idea fatal flaw / go-no-go | explorer |
| `data-researcher` | 数据集、指标和证据收集 | explorer |
| `search-specialist` | 快速检索代码或外部来源 | explorer |

## 暂不纳入

- 全量 167 个 TOML：数量过大，触发和维护成本高。
- 大批语言专家：本地已有工程 skill，遇到具体语言任务再审计。
- 默认 `workspace-write` agent：与本地写范围控制冲突，先不安装。
- `agent-installer`：安装行为需要单独批准，不能自动触发。
- 第二份 zip 的完整 `codex-subagent-orchestrator` skill：其强制 plan-first 和 plan/ 记录政策与本地默认执行习惯冲突。

## 本地裁决优先级

```text
用户当前边界
> 本地 skill 路由
> 科研/工程主流程
> 子代理并行收益
> 外部角色卡便利性
```

## 安装前审计记录模板

| 项 | 内容 |
|---|---|
| 候选 agent |  |
| 来源 zip |  |
| 原路径 |  |
| 许可证 |  |
| 是否与本地 skill 同名 |  |
| 是否与现有 TOML agent 同名 |  |
| 默认权限 | read-only / workspace-write |
| 本地定位 | explorer / worker / reviewer / reference-only |
| 是否允许安装 | yes / no |
| 理由 |  |
