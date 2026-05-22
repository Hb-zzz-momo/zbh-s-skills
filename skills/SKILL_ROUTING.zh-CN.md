# Skills 全仓库路由手册

> 目标：让 Codex 先按任务路由，再按需加载最少必要 skill，避免把 `C:\Users\zbh\.agents\skills` 当成一个平铺清单。
>
> 总控 skill：`skill-router-zh`
>
> 工程母流程：`agent-skills-ao/USAGE.zh-CN.md`

## 1. 总原则

整个 skills 库按“两层结构”使用：

1. **路由层**：`skill-router-zh`、`using-agent-skills`、`plan-faithful-execution-zh`。
2. **执行层**：科研、工程、写作、课程、调研、汇报、运维等具体 skill。

每次任务只选择必要组合：

```text
1 个主 skill + 0-2 个辅助 skill + 必要验证/审计
```

不要一次性加载全部技能。若任务跨领域，分阶段切换 skill。

## 2. 路由四步法

### Step 1：判定领域

| 领域 | 典型任务 | 首选 skill |
|---|---|---|
| 工程开发 | 读代码、改代码、接口、调试、测试、review | `project-dev-zh`, `agent-skills-ao/*` |
| 严格计划执行 | 按题面、方案、计划、prompt 文件执行 | `plan-faithful-execution-zh` |
| 科研实验 | 算法实验、smoke/formal、消融、结果收口 | `research-experiment-ops-zh` |
| 决定性审计 | formal/gate、论文主表、是否支撑 claim | `decisive-result-audit-zh` |
| 科研迭代复盘 | 判断是不是越改越差、机制是否可写 | `research-iteration-audit-zh` |
| 论文写作 | 摘要、引言、方法、实验、结论、润色 | `paper-writing-zh` |
| 翻译 | 英文学术/技术文本英译中 | `translation-zh` |
| 课程考试 | 选择题、简答题、计算题、作业 | `exam-answer-zh` |
| 课程实验 | 实验排错、截图规划、实验报告 | `lab-report-coach-zh` |
| 信息调研 | 查资料、证据链、来源核验 | `info-evidence-chain-zh` |
| PPT 汇报 | 路演、课程汇报、页面结构、故事线 | `ppt-story-design-zh` |
| 软著 | 软著项目、说明书、截图演示、代码材料 | `software-copyright-zh` |
| 长任务 | 后台任务、轮询、卡死恢复、manifest | `agent-wait-monitor-zh` |
| 产物整理 | skill-outputs、日志、旧产物归档 | `artifact-curator-zh` |
| 工作流沉淀 | SOP、流程优化、新 skill 工作流 | `workflow-forge-zh` |
| 学习复盘 | 任务结束后总结知识点 | `knowledge-digest-zh` |

### Step 2：判定阶段

| 阶段 | 目标 | 工程 skill |
|---|---|---|
| Define | 想清楚做什么、为什么做、验收什么 | `idea-refine`, `spec-driven-development` |
| Plan | 拆任务、排顺序、设检查点 | `planning-and-task-breakdown` |
| Build | 小步实现、少量改动、持续验证 | `incremental-implementation` |
| Verify | 测试、浏览器验证、复现问题 | `test-driven-development`, `browser-testing-with-devtools`, `debugging-and-error-recovery` |
| Review | 代码质量、安全、性能、简化 | `code-review-and-quality`, `security-and-hardening`, `performance-optimization`, `code-simplification` |
| Ship | Git、CI/CD、文档、上线、回滚 | `git-workflow-and-versioning`, `ci-cd-and-automation`, `documentation-and-adrs`, `shipping-and-launch` |

### Step 3：判定风险

| 风险信号 | 追加 skill |
|---|---|
| 用户给了固定计划、题面或边界 | `plan-faithful-execution-zh` |
| 结论会写进论文或报告 | `decisive-result-audit-zh`, `paper-writing-zh` |
| 改动涉及认证、权限、输入、密钥 | `security-and-hardening` |
| 页面必须真实可用 | `frontend-ui-engineering`, `browser-testing-with-devtools` |
| 性能是目标或存在回归 | `performance-optimization` |
| 任务会长时间运行 | `agent-wait-monitor-zh` |
| 需要沉淀给下一任 AI | `project-handoff-zh`, `documentation-and-adrs` |

### Step 4：声明并执行

执行前只需简短说明：

```text
Skill 路由：
- 主 skill：project-dev-zh，因为任务是代码理解和修改。
- 辅助 skill：incremental-implementation，用于小步落地。
- 收尾 skill：code-review-and-quality，用于风险审查。
```

说明后直接工作，不要把路由变成长篇计划。

## 3. 常见任务组合

### 代码修改

```text
project-dev-zh
incremental-implementation
test-driven-development
code-review-and-quality
```

默认执行方式：读现有代码 -> 小步修改 -> 跑测试/检查 -> review 风险。

### 有明确参考计划的工程任务

```text
plan-faithful-execution-zh
incremental-implementation
test-driven-development
```

默认执行方式：先锁定计划边界；缺口先问；禁止擅自扩大参数、目标、文件结构和结论。

### 前端页面

```text
frontend-ui-engineering
browser-testing-with-devtools
performance-optimization
```

默认执行方式：按真实使用场景做界面；启动本地服务；用浏览器验证交互、布局、控制台错误。

### API / 模块边界

```text
api-and-interface-design
test-driven-development
documentation-and-adrs
```

默认执行方式：先定义契约、错误语义、兼容边界，再实现和测试。

### Bug 排查

```text
debugging-and-error-recovery
test-driven-development
code-review-and-quality
```

默认执行方式：复现 -> 定位最小根因 -> 修复 -> 加回归测试 -> review。

### 科研实验

```text
research-experiment-ops-zh
plan-faithful-execution-zh
decisive-result-audit-zh
```

默认执行方式：smoke/formal 分阶段；检查 raw、summary、metric、seed、配置一致性；论文 claim 不越界。

### 论文写作

```text
paper-writing-zh
research-coach-zh
decisive-result-audit-zh
```

默认执行方式：材料驱动写作；事实、推理、建议分开；实验结论必须被结果支撑。

### 信息调研

```text
info-evidence-chain-zh
source-driven-development
```

默认执行方式：查来源、分级证据、保留链接、标注时效和不确定性。

### 汇报 / PPT

```text
ppt-story-design-zh
info-evidence-chain-zh
```

默认执行方式：先定故事线，再补证据、页面结构和讲述顺序。

### 软著

```text
software-copyright-zh
project-kickoff-delivery-zh
```

默认执行方式：定题定边界、生成可演示项目、说明书和截图材料。

### 长时间实验或后台任务

```text
agent-wait-monitor-zh
artifact-curator-zh
```

默认执行方式：后台启动、进度文件、日志轮询、卡死判断、结果归档。

## 4. 默认守门规则

以下规则优先级高于具体 skill 的便利性：

- 有参考计划时，先用 `plan-faithful-execution-zh` 锁边界。
- 有代码行为变化时，默认加入测试或可执行验证。
- 有论文/报告结论时，默认做证据和结果审计。
- 有用户指定输出目录时，写入指定目录。
- 不确定时先查 `skills/README.md`，再选择 skill。
- 一次最多主动加载 1-3 个 skill；复杂任务分阶段追加。

## 5. 给 Codex 的固定提示

可以在任务开头直接说：

```text
先用 skill-router-zh 做技能路由，只选择必要的 1-3 个 skill，然后直接执行。
```

或者：

```text
这次任务按 skills/SKILL_ROUTING.zh-CN.md 统筹，不要全量加载 skills。
```

如果任务是工程类：

```text
按 agent-skills-ao 的 Define -> Plan -> Build -> Verify -> Review -> Ship 生命周期判断阶段，再调用对应 skill。
```

## 6. 维护方式

新增、删除或修改 skill 后，运行：

```powershell
cd C:\Users\zbh\.agents\skills
.\scripts\Update-SkillsReadme.ps1
```

检查：

```powershell
Select-String -Path .\README.md -Pattern 'Skill Routing Protocol|skill-router-zh|addyosmani / agent-skills 工程工作流' -Context 0,20
```

