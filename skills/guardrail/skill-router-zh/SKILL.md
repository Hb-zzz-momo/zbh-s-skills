---
name: skill-router-zh
description: '中文 skills 总控路由技能：用于在 C:\Users\zbh\.agents\skills 中按任务领域、阶段、风险和交付物选择最少必要 skill 组合，避免一次性加载全量技能。Use when: 技能路由、选择skill、统筹skills库、该用哪个技能、组合多个skill、开始任务前分流、Codex自如使用skills、优化skills调用。不适用于：直接执行具体专业任务，路由后应切换到对应领域 skill。'
---

# Skills 总控路由

## 目标

先判断任务该走哪条流程，再只加载最少必要的 skill。默认选择 1-3 个，复杂任务最多分阶段追加，不要一次性加载整个 skills 仓库。

详细全仓库手册见：`C:\Users\zbh\.agents\skills\SKILL_ROUTING.zh-CN.md`。

## 路由流程

1. **识别任务领域**
   - 工程开发：项目理解、编码、调试、测试、review、上线；若涉及复杂工程、多方案实现、架构改造、技术 spike、工程 Gate 或候选实现池，先走 `engineering-skill-flow-zh`。
   - Web 设计 / 页面改版：网站、Landing Page、Portfolio、产品页、页面高级感、页面太丑、生成 `DESIGN.md` 时先走 `web-design-workflow-zh`；纯局部组件交互或 UI bug 再走 `frontend-ui-engineering`。
   - 科研实验：算法实验、smoke/formal、结果审计、论文 claim 边界；若涉及科研调用流、多痛点、多假设、多创新点、候选池或 Gap Gate，先走 `research-skill-flow-zh`。
   - 写作翻译：论文、翻译、报告文字。
   - 课程任务：考试、实验、实验报告。
   - 调研证据：资料收集、来源核验、证据链。
   - 汇报软著：PPT、路演、软著材料。
   - 运维产物：长任务监控、产物归档。
   - 子代理调度：`/sub`、subagents、子代理、多代理、并行委派、worker/explorer。
   - 工作流沉淀：总结流程、设计 SOP、生成新 skill。

2. **识别任务阶段**
   - Define：想清楚目标、问题、验收标准。
   - Plan：拆任务、排步骤、定义检查点。
   - Build：实现、修改、生成产物。
   - Verify：跑测试、复现、浏览器验证、结果核查。
   - Review：审查风险、简化、性能、安全。
   - Ship：提交、发布、交接、归档。

3. **选择最小 skill 组合**
   - 一个主 skill 负责领域。
   - 一个工程/验证 skill 负责落地。
   - 必要时加一个审计/守门 skill 控风险。

4. **执行前声明路由**
   - 简短说明选择哪些 skill、为什么选、哪些明显不加载。
   - 如果任务边界缺失且风险高，先问具体问题。
   - 如果边界清楚，直接执行。

## 默认组合

### 普通代码改动

```text
incremental-implementation
test-driven-development
code-review-and-quality
```

### 有参考计划或用户强调不要自作主张

```text
plan-faithful-execution-zh
incremental-implementation
code-review-and-quality
```

### 子代理 / 多代理委派

```text
subagent-orchestration-zh
```

默认执行方式：先确认用户是否明确授权真实子代理；未授权时只给本地执行方案，不 spawn。授权后父代理保留主 skill、写范围、集成和验收；子代理默认使用只读 explorer/reviewer。当父代理明确给出最小任务、唯一写范围、禁止越界规则、验证命令和回收门槛时，可以使用 worker 修改文件，且 worker 改动必须由父代理复核、集成、测试和最终验收。

### 中文项目理解和工程开发

```text
project-dev-zh
incremental-implementation
test-driven-development
```

### Web 设计 / 页面改版

```text
web-design-workflow-zh
frontend-ui-engineering
browser-testing-with-devtools
```

默认执行方式：新建网站、Landing Page、Portfolio、产品页或大改版先走 `DESIGN.md`，再审美守门、工程实现、浏览器验收；局部 UI bug 不强行重建全站设计。

### 复杂工程 / 多方案实现调用流

```text
engineering-skill-flow-zh
```

默认执行方式：先做 Project Intake、Solution Gate 和候选实现池；进入 Main Build 前收敛到一个主实现路径或明确组合路径；每阶段最多 2 个辅助 skill，审计/验证 skill 只在触发条件满足时调用。

### 科研多候选探索 / 调用流

```text
research-skill-flow-zh
```

默认执行方式：先做 Memory Intake、Gap Gate 和候选池，再按阶段切换到唯一主 skill；每阶段最多 2 个辅助 skill，审计 skill 只在触发条件满足时调用。

### 科研算法实验

```text
research-experiment-ops-zh
agent-wait-monitor-zh
artifact-curator-zh
```

默认执行方式：smoke/dev/formal 分阶段执行；固定计划时触发 `plan-faithful-execution-zh`，formal、冻结版本或论文 claim 时触发 `decisive-result-audit-zh`。

### 论文/报告文字

```text
paper-writing-zh
research-coach-zh
plan-faithful-execution-zh
```

### 信息调研

```text
info-evidence-chain-zh
source-driven-development
```

### PPT/软著

按实际任务二选一，不要同时加载无关技能。

```text
ppt-story-design-zh
software-copyright-zh
```

### 长任务

```text
agent-wait-monitor-zh
artifact-curator-zh
```

## 工程生命周期映射

| 阶段 | 首选 skill |
|---|---|
| Define | `idea-refine`, `spec-driven-development` |
| Plan | `planning-and-task-breakdown`, `plan-faithful-execution-zh` |
| Build | `incremental-implementation`, `project-dev-zh` |
| Verify | `test-driven-development`, `browser-testing-with-devtools`, `debugging-and-error-recovery` |
| Review | `code-review-and-quality`, `security-and-hardening`, `performance-optimization`, `decisive-result-audit-zh` |
| Ship | `git-workflow-and-versioning`, `ci-cd-and-automation`, `shipping-and-launch`, `documentation-and-adrs` |

复杂工程任务先用 `engineering-skill-flow-zh` 做阶段总控；普通小改仍直接走对应阶段 skill。

## 不要这样用

- 不要把所有 skill 都加载进上下文。
- 不要只按 skill 名字猜，优先读 `skills/README.md` 的场景分组和触发词。
- 不要用工程 review skill 替代科研结果审计。
- 不要用论文写作 skill 编造实验结果。
- 不要把工程总控流当成普通小修入口；单文件小改、明确 bug fix 或直接代码解释仍走轻量工程 skill。
- 不要把“深入分析”自动等同于授权子代理；只有用户明确要求 subagent、`/sub`、并行委派或多代理时才真实调度。
- 不要在参考计划不完整时自行扩展关键参数、结论或文件结构。

## 输出格式

开始执行前，用 2-4 行给出：

```text
Skill 路由：
- 主 skill：...
- 辅助 skill：...
- 不加载：...，原因是...
```

随后按被选中的具体 skill 执行，而不是停留在路由说明。
