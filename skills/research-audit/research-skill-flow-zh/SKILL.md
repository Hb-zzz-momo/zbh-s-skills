---
name: research-skill-flow-zh
description: 科研 Skill 调用流总控技能：用于多痛点、多假设、多创新点的科研任务分阶段路由、候选池生成、Gap Gate、候选 smoke 漏斗、dev/formal 收敛、论文 claim 分级和外部科研 skill 冲突审计。Use when: 科研调用流、科研skill路由、多候选科研流程、多痛点、多假设、多创新点、候选池、Gap Gate、Memory Intake、Candidate Smoke Funnel、论文claim分级、外部科研skill冲突审计。不适用于：直接执行单一实验、单篇论文写作或普通工程开发，路由后应切换到对应阶段主 skill。
argument-hint: "说明科研阶段和材料，例如：按科研调用流做新方向探索；用多候选漏斗筛选这些创新点；论文前按 claim 分级整理"
---

# 科研 Skill 调用流

## 目标

把科研任务组织成“多候选生成 + 分阶段筛选 + 单实验验证”的调用流。早期允许提出多个痛点、多个假设、多个创新点；进入实验和论文 claim 前必须收敛，避免把多个机制一次混改后直接宣称整体有效。

本 skill 是科研路由和流程守门，不替代阶段主 skill。选定阶段后，按下表切换到对应主 skill 执行。

## 调用预算硬规则

每个科研任务阶段只能使用：

```text
1 个主 skill + 最多 2 个辅助 skill + 条件触发审计 skill
```

- 主 skill：负责当前阶段的判断和产出。
- 辅助 skill：只补充资料、模板、监控、归档或统计，不覆盖主流程。
- 审计 skill：不计入辅助数量，但只有触发条件满足时才能调用。
- 跨阶段任务要分阶段切换主 skill，不要一次性加载全量科研 skill。

## 阶段路由

| 阶段 | 主 skill | 最多辅助 skill | 条件审计 skill | 必须产出 |
|---|---|---|---|---|
| Memory Intake | `research-coach-zh` | `info-evidence-chain-zh`, `literature-triage-matrix` | 无 | 项目状态卡、文献比较矩阵、候选池初稿 |
| Gap Gate | `research-coach-zh` | `literature-triage-matrix`, `info-evidence-chain-zh` | `iteration-reflection-guard-zh` | 候选池表、PASS/CAUTION/BLOCK |
| Research Design | `research-coach-zh` | `research-design-helper`, `literature-triage-matrix` | `plan-faithful-execution-zh` | 创新点可行性矩阵、最小验证计划 |
| Candidate Smoke Funnel | `research-experiment-ops-zh` | `agent-wait-monitor-zh`, `artifact-curator-zh` | `research-iteration-audit-zh` | 每个候选的独立 smoke 记录和排序 |
| Dev/Formal | `research-experiment-ops-zh` | `agent-wait-monitor-zh`, `artifact-curator-zh` | `decisive-result-audit-zh`, `plan-faithful-execution-zh` | dev/formal 结果、raw/summary/config 对齐检查 |
| Paper Memory/Writing | `paper-writing-zh` | `paper-memory-builder`, `research-statistics-reporting-zh` | `decisive-result-audit-zh` | claim 分级、`.paper/claims.yml`、`.paper/figures.yml` |
| Handoff/Archive | `project-handoff-zh` | `artifact-curator-zh` | 无 | 接班文档、产物索引、下一轮约束 |

若外部辅助 skill 未安装或不可用，只保留其方法定位，不新建同名本地 skill，不影响本地主流程执行。

## 1. Memory Intake

主 skill：`research-coach-zh`

读取：

- 历史实验记录。
- 实验日志、summary、raw。
- 既有失败路线和有效路线。
- 文献材料、证据链和文献比较矩阵。
- 用户指定边界、数据、算力、时间和论文目标。

项目状态卡必须保留六段式记忆：

```text
尝试方法
计划
脚本/命令
结果
经验
下次必须继承的约束
```

新增候选记录区：

```text
候选痛点列表
候选假设列表
候选创新点列表
每个候选对应的证据、风险和验证方式
```

## 2. Gap Gate

主 skill：`research-coach-zh`

使用多候选 gate，不把候选提前压成单痛点或单假设：

| Gate | 判断问题 | 依据 |
|---|---|---|
| Gate 1 | 每个痛点对应的 gap 是否存在？ | 文献矩阵参考 |
| Gate 2 | 每个创新点是否构成真实贡献？ | 文献对比辅助 |
| Gate 3 | 每个候选以当前数据、算力、时间是否可行？ | 本地实验经验为主 |

候选池表模板：

| 候选ID | 痛点 | 假设 | 创新点 | 文献支持 | 本地可行性 | 预期收益 | 实现成本 | 风险等级 | 建议动作 |
|---|---|---|---|---|---|---|---|---|---|
| C1 |  |  |  |  |  |  |  |  | PASS / CAUTION / BLOCK |

建议动作含义：

- PASS：进入最小 smoke 设计。
- CAUTION：保留，但必须先补证据或缩小实现。
- BLOCK：暂不实验，写入失败路线或未来工作。

## 3. Research Design

主 skill：`research-coach-zh`

外部 `research-design-helper` 只能提供设计模板和问题收敛参考：

```text
研究问题
候选痛点
候选假设
候选机制
可识别性
验证计划
风险登记
```

设计阶段必须产出创新点可行性矩阵：

| 创新点 | 对应痛点 | 预期机制 | 可独立实现 | 可独立消融 | smoke 成本 | 失败条件 |
|---|---|---|---|---|---|---|

筛选规则：

- 初始可以保留多个候选。
- 进入 smoke 前必须给每个候选定义最小验证。
- dev/formal 前必须收敛到一个主候选或一个明确组合候选。
- 组合候选必须说明为什么不能拆开验证。

## 4. Candidate Smoke Funnel

主 skill：`research-experiment-ops-zh`

实验执行采用候选漏斗：

```text
候选池
-> 每个候选独立 smoke
-> smoke 结果排序
-> 选择 1 个主候选进入 dev
-> dev 通过后进入 formal
-> formal 后审计 claim
```

硬规则：

- smoke 可以并行多个候选。
- 每个 smoke 只验证一个主候选，或一个明确声明的组合候选。
- dev/formal 不允许未记录的混合机制。
- formal 前不得事后改 gate。
- 不允许把多个创新点一次性混改后直接宣称整体有效。
- 外部 two-loop 只作为节奏参考，不替代本地 smoke/dev/formal。

候选独立记录必须包含：

```text
动机
对应痛点
核心假设
预期收益
实现成本
可消融方式
失败条件
脚本/命令
raw/summary/config 路径
结论边界
```

## 5. 审计触发

| 审计 skill | 触发条件 |
|---|---|
| `decisive-result-audit-zh` | 结果影响论文、formal/gate、冻结版本、主表、是否停止迭代、是否声称胜过基线 |
| `research-iteration-audit-zh` | 机制堆叠、连续失败、创新点说不清、runtime 膨胀、性能退化、研究债务增加 |
| `plan-faithful-execution-zh` | 用户给出固定计划、题面、实验计划、边界锁定或禁止自我扩展 |
| `iteration-reflection-guard-zh` | 继续迭代、提出下一轮方向、避免重复失败、检查创新性和致命痛点 |

审计只在触发时调用，不占辅助 skill 数量，但审计结论必须写入本轮记录。

## 6. Paper Memory / Writing

主 skill：`paper-writing-zh`

论文前必须把多个创新点分级：

```text
主创新点：formal 证据支持，可进入摘要、方法、贡献
次创新点：dev 或消融支持，只能谨慎写
失败候选：写入局限或未来工作，不能包装成贡献
放弃候选：进入经验记录
```

`.paper/claims.yml` 每条 claim 必须标记：

```yaml
claims:
  - id: C1
    text: ""
    status: supported # supported | draft | rejected | gap
    evidence:
      formal: ""
      audit: ""
    boundary: ""
```

没有 formal 或审计支持的创新点不能写成正式贡献。

## 7. 外部候选策略

第一批只允许作为候选辅助或方法参考：

| 候选 | 用途 | 本地定位 |
|---|---|---|
| `literature-triage-matrix` | 文献比较矩阵 | 辅助 gap 判断 |
| `research-design-helper` | 多痛点、多假设设计模板 | 辅助研究设计 |
| `paper-memory-builder` | claim/figure 记忆 | 辅助论文写作 |
| `research-context-compressor` | `.research/` manifest | 可选补充，不替代六段式记忆 |
| `research-project-orienter` | 项目快速接班 memo | 可选补充 `project-handoff-zh` |

暂不直接纳入：

- `autoresearch`：自治原则冲突，只吸收 two-loop 思路。
- `academic-research-suite`：体量过大，只吸收 pipeline/integrity gate 思路。
- 大量模型训练工具 skill：遇到具体模型任务时再单独审计。

## 8. 冲突审计

任何外部 skill 后续安装或本地化前，必须审计：

| 审计项 | 规则 |
|---|---|
| 名称冲突 | 不允许与现有本地 skill 同名 |
| 职责冲突 | 本地已有主 skill 时，外部只能辅助 |
| 候选机制冲突 | 外部不得要求一次混改多个机制并直接 claim |
| 记忆冲突 | 不允许替换六段式记忆 |
| 执行冲突 | 不允许替代 smoke/dev/formal |
| 审计冲突 | 不允许绕过结果审计和迭代审计 |
| 输出冲突 | 不允许破坏 `skill-outputs/<skill-name>/` |
| 许可证冲突 | 必须记录来源、许可证、是否可再分发 |

裁决优先级：

```text
本地已验证规则
> 用户固定边界
> 多候选可比较性
> 结果可复现性
> 外部自动化效率
```

## 9. 输出格式

执行科研任务前先输出 2-5 行路由：

```text
Skill 路由：
- 阶段：...
- 主 skill：...
- 辅助 skill：...
- 审计 skill：未触发 / 已触发，原因是...
```

随后直接进入对应阶段主 skill 执行。阶段结束时必须更新：

- 六段式项目状态卡。
- 候选池状态。
- 已触发审计及结论。
- 下一阶段唯一主候选或明确组合候选。

## 10. 自检清单

收尾前检查：

- 每个阶段只有 1 个主 skill。
- 辅助 skill 不超过 2 个。
- 审计 skill 只在触发条件满足时调用。
- 多个创新点都有独立证据和失败条件。
- dev/formal 没有未记录的混合机制。
- 未验证候选没有写成正式论文贡献。
- 六段式记忆被保留并更新。
