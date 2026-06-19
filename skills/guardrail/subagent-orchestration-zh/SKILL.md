---
name: subagent-orchestration-zh
description: "中文子代理编排技能：用于把 Codex subagents、/sub、多代理协调、并行委派、explorer/worker、TOML agent、awesome-codex-subagents 角色库和本地 skills 路由结合起来；约束何时允许真实 spawn 子代理、何时只给委派方案、如何划分父代理/子代理职责、如何避免写范围冲突、如何把科研与工程任务的子代理结果回收到本地审计和验收流程。Use when: subagent, subagents, /sub, 子代理, 多代理, 多代理协调, 并行代理, 并行委派, 委派执行, worker, explorer, spawn_agent, TOML agent, awesome-codex-subagents, Codex-Subagent-Orchestrator, 子代理审计, 子代理调度。不适用于：用户没有明确要求子代理或并行委派的普通深入分析、普通代码修改、普通科研实验；这些任务应继续走本地领域 skill。"
---

# 子代理编排

## 目标

把 subagent 顺畅接入本地 `skills/`，但不让它成为新的总控中枢。

本 skill 只负责子代理调度、委派边界、运行证据和验收回收；科研、工程、写作、审计仍由本地领域 skill 主导。

## 来源边界

- `awesome-codex-subagents-main.zip`：角色卡库，可作为精选 TOML agent 候选和 persona 参考，不批量导入。
- `Codex-Subagent-Orchestrator-main.zip`：父代理调度和 run-kit 参考，只吸收流程思想，不照搬强制 plan-first 政策。
- 本地 `skills/`：最高优先级的工作流和审计体系。

详细来源、许可证和候选角色见 `references/subagent-role-catalog.md`。

## 硬规则

1. 只有用户明确要求 `subagent`、`/sub`、子代理、多代理、并行代理、委派或 worker/explorer 时，才允许真实调度子代理。
2. “深入分析”“全面分析”“仔细检查”本身不等于授权开子代理。
3. 父代理保留任务解释、skill 路由、写范围裁决、最终集成、验收和论文 claim 边界。
4. 子代理默认使用只读 explorer/reviewer；当父代理明确给出最小任务、唯一写范围、禁止越界规则、验证命令和回收门槛时，可以使用 worker 修改文件。
5. 一次默认最多 3 个子代理。超过 3 个必须说明真实并行收益和集成成本。
6. 子代理结论不能自动升级为 formal 结果、论文贡献、发布判断或最终验收。
7. 不安装、不解压、不批量复制外部 zip，除非用户后续明确要求安装并通过冲突审计。

## 路由关系

### 工程任务

主流程仍按 `agent-skills-ao` 生命周期和本地工程 skill：

```text
Define -> Plan -> Build -> Verify -> Review -> Ship
```

subagent 只做 sidecar：

- explorer：代码路径映射、接口边界、测试缺口、风险面扫描。
- worker：独立模块实现、独立测试补充、互不重叠的文件范围。
- reviewer：最后只读 review，检查回归、scope drift、缺测试、风险。

### 科研任务

主流程仍由 `research-skill-flow-zh` 控制：

```text
Memory Intake -> Gap Gate -> Research Design -> Candidate Smoke Funnel -> Dev/Formal -> Paper Memory
```

subagent 可用于：

- 并行读文献和证据链。
- 并行读历史实验、日志、raw、summary。
- 检查候选创新点的证据、风险和失败条件。
- 审计 raw/summary/config 是否一致。

formal、freeze、论文 claim 必须回到 `decisive-result-audit-zh`。

### 长任务

`agent-wait-monitor-zh` 管后台进程、日志、进度文件、卡死判断和续跑。  
本 skill 只管多代理分工，不替代 wait/monitor。

## 调度流程

1. **确认授权**
   - 用户是否明确要求 subagent 或并行委派。
   - 若没有授权，输出本地执行方案，不真实 spawn。

2. **选主 skill**
   - 工程：按 `skill-router-zh` 和 `agent-skills-ao` 选阶段主 skill。
   - 科研：优先 `research-skill-flow-zh` 或对应科研阶段主 skill。
   - 计划边界：用户给了固定计划时加入 `plan-faithful-execution-zh`。

3. **拆父子职责**
   - 父代理做关键路径和最终验收。
   - 子代理只做可并行、边界清晰、不会阻塞父代理下一步的任务。

4. **确定子代理类型**
   - explorer：只读，回答一个具体问题。
   - reviewer：只读，通常放在最后，检查回归、scope drift、缺测试和风险。
   - worker：可写，必须有父代理规定好的最小修改、唯一写范围、禁止越界规则、验证命令和回收门槛。

5. **写委派任务卡**
   - 使用 `references/delegation-templates.md`。
   - 每个子代理必须有 objective、input context、write scope、expected output、wait rule、integration gate。

6. **执行与等待**
   - 父代理不能把立即阻塞任务交给子代理后空等。
   - `wait_agent` 只在下一步必须依赖结果时使用。
   - 子代理运行时，父代理做不重叠的本地工作。

7. **回收与验收**
   - 子代理结果先进入父代理审查。
   - worker 改动必须由父代理检查、集成和验证。
   - 科研结论按本地审计 skill 决定 claim 等级。

## 写范围规则

worker 改动必须由父代理复核、集成、测试和最终验收；子代理不得自行扩大任务、替代父代理裁决或把改动升级为最终结论。

允许并行 worker 的条件：

- 文件集合不重叠。
- 不同时修改同一接口、配置、schema、实验口径或公共常量。
- 任何一个 worker 失败都不会污染另一个 worker 的验收。
- 父代理能描述确定的合并顺序和冲突处理。

必须退化为单 worker 或串行的条件：

- 两个 worker 可能改同一文件。
- 一个改动依赖另一个先落地。
- 涉及共享 contract、metric、collector、配置、论文 claim 或发布面。
- 合并成本高于并行收益。

## 运行证据

substantial 子代理运行可以写入：

```text
skill-outputs/subagent-orchestration-zh/<中文主题_YYYYMMDD_HHMMSS>/
```

或任务工作区：

```text
subagent-runs/<run-id>/
```

推荐文件：

```text
orchestration-plan.md
status.md
worker-briefs/<worker>.md
results/<worker>.md
review-verdict.md
acceptance.md
```

不要强制所有编码任务写 `plan/`。有参考计划或固定边界时，使用 `plan-faithful-execution-zh` 锁边界即可。

## 冲突审计

安装或本地化外部 subagent 前必须审计：

| 审计项 | 规则 |
|---|---|
| 名称冲突 | 不覆盖现有 `~/.codex/agents/*.toml`、项目 `.codex/agents/*.toml` 或本地 skill 名 |
| 职责冲突 | 不让外部 agent 替代本地领域主 skill |
| 权限冲突 | 默认使用只读 explorer/reviewer；worker 可写必须有最小任务、唯一写范围、禁止越界规则、验证命令和回收门槛 |
| 记忆冲突 | 不替代科研六段式记忆或项目 handoff |
| 审计冲突 | 不绕过 `decisive-result-audit-zh`、`research-iteration-audit-zh`、`code-review-and-quality` |
| 输出冲突 | 不破坏 `skill-outputs/<skill-name>/` 和任务工作区产物结构 |
| 许可证冲突 | 记录来源、许可证、版权、是否可再分发 |

运行只读审计：

```powershell
powershell -ExecutionPolicy Bypass -File skills/guardrail/subagent-orchestration-zh/scripts/audit_subagent_sources.ps1
```

## 参考文件

- `references/subagent-role-catalog.md`：来源、候选角色、许可证和纳入策略。
- `references/delegation-runbook.md`：父代理调度流程和工程/科研场景。
- `references/delegation-templates.md`：委派任务卡、结果、review 和 acceptance 模板。

## 输出格式

真实调度前先输出：

```text
Subagent 路由：
- 授权：是/否，依据是...
- 本地主 skill：...
- 子代理：explorer/worker/reviewer，数量...
- 写范围：...
- 回收审计：...
```

如果未授权真实 subagent：

```text
Subagent 路由：
- 授权：否
- 处理方式：只给本地执行方案 / 不 spawn
```

## 收尾自检

- 是否只有明确授权时才真实调度。
- 是否父代理保留最终集成和验收。
- 是否 worker 写范围互斥。
- 是否没有用子代理替代本地科研/工程/审计主流程。
- 是否记录了来源和许可证边界。
