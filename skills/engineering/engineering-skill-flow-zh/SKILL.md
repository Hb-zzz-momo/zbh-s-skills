---
name: engineering-skill-flow-zh
description: "中文工程 Skill 调用流总控技能：用于复杂工程实现、多方案工程设计、架构改造、跨文件功能开发、技术 spike、候选实现筛选、工程 Gate、增量切片、验证审计和交付记忆。Use when: 工程调用流、工程skill路由、多方案实现、实现候选池、技术spike、工程Gate、复杂工程任务、架构改造、多文件开发、候选方案筛选、Define Plan Build Verify Review Ship 优化。不适用于：单文件小修、普通代码解释、直接执行已明确的简单任务；路由后应切换到对应阶段主 skill。"
metadata:
  argument-hint: "说明工程目标和边界，例如：按工程调用流实现这个功能；先比较多个实现方案再开发；这个架构改造先做 Gate 和 spike"
---

# 工程 Skill 调用流

## 目标

把复杂工程任务组织成“多方案生成 + 分阶段筛选 + 单主路径实现”的调用流。早期允许提出多个问题、多个实现方案、多个技术路径；进入正式 Build 前必须收敛，避免把重构、新功能、性能优化、顺手清理混在一次改动里直接宣称完成。

本 skill 是工程路由和流程守门，不替代阶段主 skill。选定阶段后，按下表切换到对应主 skill 执行。

## 调用预算硬规则

每个工程任务阶段只能使用：

```text
1 个主 skill + 最多 2 个辅助 skill + 条件触发审计/验证 skill
```

- 主 skill：负责当前阶段的判断和产出。
- 辅助 skill：只补充上下文、契约、文档、监控、归档或专项实现建议。
- 审计/验证 skill：不计入辅助数量，但只有触发条件满足时调用。
- 跨阶段任务要分阶段切换主 skill，不要一次性加载全量工程 skill。

## 阶段路由

| 阶段 | 主 skill | 最多辅助 skill | 条件审计/验证 skill | 必须产出 |
|---|---|---|---|---|
| Project Intake | `project-dev-zh` | `context-engineering`, `source-driven-development` | `plan-faithful-execution-zh` | 项目状态卡、边界锁、候选问题列表 |
| Solution Gate | `planning-and-task-breakdown` | `api-and-interface-design`, `project-dev-zh` | `doubt-driven-development` | 候选实现表、PASS/CAUTION/BLOCK |
| Implementation Design | `spec-driven-development` | `api-and-interface-design`, `documentation-and-adrs` | `plan-faithful-execution-zh` | 主路径设计、接口契约、验收标准 |
| Candidate Spike / Slice Funnel | `incremental-implementation` | `test-driven-development`, `source-driven-development` | `debugging-and-error-recovery` | 每个候选的最小验证记录和排序 |
| Main Build | `incremental-implementation` | `test-driven-development`, `project-dev-zh` | `security-and-hardening`, `performance-optimization` | 主实现路径、测试结果、改动清单 |
| Verify / Review | `code-review-and-quality` | `test-driven-development`, `browser-testing-with-devtools` | `security-and-hardening`, `performance-optimization` | 验证证据、风险审查、未覆盖项 |
| Ship / Memory | `git-workflow-and-versioning` | `documentation-and-adrs`, `project-handoff-zh` | `ci-cd-and-automation`, `shipping-and-launch` | 提交/交付说明、运行命令、接班约束 |

## 1. Project Intake

主 skill：`project-dev-zh`

读取：

- 用户目标、验收标准、禁止事项和指定输出目录。
- 现有项目结构、入口、关键模块、接口契约和测试方式。
- 历史计划、报错、日志、已失败路线和用户固定边界。
- 当前 git 状态，区分本次修改和用户已有改动。

项目状态卡保留六段式记忆：

```text
尝试方法
计划
脚本/命令
结果
经验
下次必须继承的约束
```

新增工程候选区：

```text
候选问题列表
候选实现方案列表
候选技术路径列表
每个候选对应的证据、风险、影响面和验证方式
```

## 2. Solution Gate

主 skill：`planning-and-task-breakdown`

使用多方案 gate，不把复杂任务提前压成单一实现：

| Gate | 判断问题 | 依据 |
|---|---|---|
| Gate 1 | 问题是否真实存在且属于本次范围？ | 用户需求、代码路径、日志、现有行为 |
| Gate 2 | 方案是否满足契约且不破坏现有逻辑？ | 接口、类型、配置、调用链、兼容边界 |
| Gate 3 | 当前时间、测试条件和回滚能力是否支持落地？ | 改动范围、测试成本、依赖风险、回滚难度 |

候选实现表模板：

| 候选ID | 问题 | 实现方案 | 影响文件/模块 | 契约影响 | 测试方式 | 回滚难度 | 实现成本 | 风险等级 | 建议动作 |
|---|---|---|---|---|---|---|---|---|---|
| E1 |  |  |  |  |  |  |  |  | PASS / CAUTION / BLOCK |

建议动作含义：

- PASS：进入 spike 或最小切片。
- CAUTION：保留，但必须先补契约、缩小范围或补测试。
- BLOCK：本轮不做，写入风险或后续任务。

## 3. Implementation Design

主 skill：`spec-driven-development`

设计阶段必须产出工程可行性矩阵：

| 方案 | 对应问题 | 预期效果 | 可独立实现 | 可独立测试 | spike 成本 | 回滚方式 | 失败条件 |
|---|---|---|---|---|---|---|---|

筛选规则：

- 初始可以保留多个候选。
- 进入 spike 前必须给每个候选定义最小验证。
- 进入 Main Build 前必须收敛到一个主实现路径或一个明确组合路径。
- 组合路径必须说明为什么不能拆开验证或串行落地。

## 4. Candidate Spike / Slice Funnel

主 skill：`incremental-implementation`

工程执行采用候选漏斗：

```text
候选池
-> 每个候选独立 spike 或最小切片
-> 结果排序
-> 选择 1 个主实现路径进入 Main Build
-> 小步实现并验证
-> Review 后 Ship
```

硬规则：

- spike 可以并行多个候选，但只允许读写互斥或明确隔离的范围。
- 每个 spike 只验证一个主候选，或一个明确声明的组合候选。
- Main Build 不允许未记录的混合机制。
- 正式实现前不得事后改 gate 来合理化已经写下的代码。
- 不允许把多个未验证改动一次性混改后直接宣称整体有效。

候选独立记录必须包含：

```text
动机
对应问题
核心方案
预期效果
实现成本
影响文件
可测试方式
失败条件
脚本/命令
验证结果
结论边界
```

## 5. Main Build

主 skill：`incremental-implementation`

进入 Main Build 后：

- 只实现已通过 gate 的主路径。
- 按垂直切片或风险优先切片推进。
- 每个切片都要保持项目可运行或明确用 feature flag 隔离。
- 不顺手清理无关文件，不借功能开发做大重构。
- 如果出现新问题，先记录为新候选，不自动扩展当前实现范围。

## 6. 审计和验证触发

| 审计/验证 skill | 触发条件 |
|---|---|
| `plan-faithful-execution-zh` | 用户给出固定计划、题面、prompt、边界锁定或禁止自我扩展 |
| `doubt-driven-development` | 非平凡架构决策、候选方案分歧大、证据不足但想继续 |
| `debugging-and-error-recovery` | 测试失败、构建失败、行为不符合预期或根因不明 |
| `security-and-hardening` | 认证、权限、用户输入、密钥、外部数据、依赖或网络边界变化 |
| `performance-optimization` | 性能是目标、热路径变化、指标回归或连续优化停滞 |
| `code-review-and-quality` | 完成一个实现切片、准备合并、准备交付或需要独立风险审查 |
| `browser-testing-with-devtools` | 页面、交互、布局、网络请求或真实浏览器行为是验收条件 |

审计只在触发时调用，不占辅助 skill 数量，但审计结论必须写入本轮记录。

## 7. Ship / Memory

主 skill：`git-workflow-and-versioning`

交付前必须把实现声明分级：

```text
已验证功能：有命令、测试、日志或截图支持，可作为正式交付说明
已实现未充分验证：代码已改，但证据不足，只能谨慎说明
失败候选：写入风险、后续任务或经验记录，不能包装成已完成
放弃候选：进入经验记录，不再换名字重复实现
```

工程交付记录必须包含：

```text
改动文件
运行命令
测试/验证结果
未覆盖风险
回滚方式
下次必须继承的约束
```

## 8. 输出格式

执行复杂工程任务前先输出 2-5 行路由：

```text
Skill 路由：
- 阶段：...
- 主 skill：...
- 辅助 skill：...
- 审计/验证 skill：未触发 / 已触发，原因是...
```

随后直接进入对应阶段主 skill 执行。阶段结束时必须更新：

- 六段式项目状态卡。
- 候选实现池状态。
- 已触发审计/验证及结论。
- 下一阶段唯一主实现路径或明确组合路径。

## 9. 自检清单

收尾前检查：

- 每个阶段只有 1 个主 skill。
- 辅助 skill 不超过 2 个。
- 审计/验证 skill 只在触发条件满足时调用。
- 多个实现候选都有独立证据和失败条件。
- Main Build 没有未记录的混合机制。
- 未验证候选没有写成正式交付成果。
- 六段式工程记忆被保留并更新。
