# agent-skills-ao 使用指南

> 适用目录：`C:\Users\zbh\.agents\skills\agent-skills-ao`
>
> 依据：`agent-skills-github.md` 中对 `addyosmani/agent-skills` 的定位、Define -> Plan -> Build -> Verify -> Review -> Ship 生命周期，以及本目录已安装的 22 个工程工作流 skill。

## 1. 这套 skill 的定位

`agent-skills-ao` 是一套软件工程工作流 skill 包，不是“越多越好”的提示词集合。它的核心用途是把 AI 开发任务放进一个可控流程：

```text
Define 定义 -> Plan 计划 -> Build 开发 -> Verify 验证 -> Review 评审 -> Ship 发布
```

日常使用时，不需要一次性加载全部 22 个 skill。更稳妥的方式是：

1. 先判断当前任务处在哪个阶段。
2. 只点名当前阶段需要的 1-3 个 skill。
3. 对高风险任务再叠加安全、性能、文档或怀疑式复核 skill。

## 2. 在 Codex/Agent 里怎么调用

本目录已经按 skill 子目录安装完成。使用时直接在请求里点名 skill 即可，例如：

```text
使用 test-driven-development，先为这个登录功能写失败测试，再实现代码。
```

```text
使用 code-review-and-quality，review 当前 diff，优先找 bug、回归风险和缺失测试。
```

```text
使用 incremental-implementation，把这个功能按小步可验证方式完成，每一步都跑必要检查。
```

如果不确定该用哪个，可以先调用 meta skill：

```text
先根据 using-agent-skills 判断这次任务应该走哪些工程 skill，然后再开始做。
```

## 3. 生命周期选型表

| 阶段 | Skill | 用来做什么 | 典型调用方式 |
|---|---|---|---|
| Meta | `using-agent-skills` | 判断当前任务该用哪些 skill | 先判断这次任务该走哪个工作流 |
| Define | `idea-refine` | 把模糊想法收敛成可执行方案 | 用 idea-refine 帮我把这个功能想清楚 |
| Define | `spec-driven-development` | 先写规格、验收标准，再编码 | 使用 spec-driven-development，先输出 SPEC |
| Plan | `planning-and-task-breakdown` | 把需求拆成任务、依赖和验收标准 | 用 planning-and-task-breakdown 拆任务 |
| Build | `incremental-implementation` | 小步实现、小步验证 | 按 incremental-implementation 一次只改一个垂直切片 |
| Build | `test-driven-development` | 先测试再实现，防回归 | 用 test-driven-development 先写失败测试 |
| Build | `context-engineering` | 整理上下文，减少 AI 猜测 | 用 context-engineering 梳理这个仓库需要的上下文 |
| Build | `source-driven-development` | 基于官方文档实现 | 用 source-driven-development 查官方文档后再改 |
| Build | `doubt-driven-development` | 高风险方案反证复核 | 用 doubt-driven-development 审一遍这个方案 |
| Build | `frontend-ui-engineering` | 前端组件、布局、交互、响应式 | 用 frontend-ui-engineering 优化这个页面 |
| Build | `api-and-interface-design` | API、模块边界、接口契约 | 用 api-and-interface-design 设计这个接口 |
| Verify | `browser-testing-with-devtools` | 真实浏览器验证、DOM、网络、控制台 | 用 browser-testing-with-devtools 验证页面交互 |
| Verify | `debugging-and-error-recovery` | 复现、定位、最小修复、加保护 | 用 debugging-and-error-recovery 查这个 bug |
| Review | `code-review-and-quality` | 多维代码审查 | 用 code-review-and-quality review 当前 diff |
| Review | `code-simplification` | 降复杂度，保持行为不变 | 用 code-simplification 简化这段代码 |
| Review | `security-and-hardening` | 输入、认证、依赖、密钥、安全边界 | 用 security-and-hardening 做安全审查 |
| Review | `performance-optimization` | 性能 profiling、瓶颈、Web Vitals | 用 performance-optimization 找性能瓶颈 |
| Ship | `git-workflow-and-versioning` | 提交、分支、版本、变更组织 | 用 git-workflow-and-versioning 规划提交 |
| Ship | `ci-cd-and-automation` | CI/CD、质量门禁、自动化发布 | 用 ci-cd-and-automation 设计 GitHub Actions |
| Ship | `deprecation-and-migration` | 迁移、废弃、兼容、清理旧代码 | 用 deprecation-and-migration 做迁移计划 |
| Ship | `documentation-and-adrs` | ADR、API 文档、设计原因沉淀 | 用 documentation-and-adrs 写 ADR |
| Ship | `shipping-and-launch` | 发布检查、灰度、回滚、监控 | 用 shipping-and-launch 做上线 checklist |

## 4. 推荐常驻组合

日常代码任务优先常驻这 3 个：

```text
incremental-implementation
test-driven-development
code-review-and-quality
```

原因很直接：

- `incremental-implementation` 控制改动粒度，避免一次性大改。
- `test-driven-development` 给行为变化建立验证锚点。
- `code-review-and-quality` 在收尾时找 bug、回归风险和测试缺口。

## 5. 按任务叠加的组合

新功能从零开始：

```text
spec-driven-development
planning-and-task-breakdown
incremental-implementation
test-driven-development
code-review-and-quality
```

前端页面或交互：

```text
frontend-ui-engineering
browser-testing-with-devtools
performance-optimization
```

API 或模块边界：

```text
api-and-interface-design
test-driven-development
documentation-and-adrs
```

线上 bug 或构建失败：

```text
debugging-and-error-recovery
test-driven-development
code-review-and-quality
```

安全敏感功能：

```text
security-and-hardening
doubt-driven-development
code-review-and-quality
```

准备发布：

```text
git-workflow-and-versioning
ci-cd-and-automation
shipping-and-launch
documentation-and-adrs
```

迁移或删除旧系统：

```text
deprecation-and-migration
test-driven-development
shipping-and-launch
documentation-and-adrs
```

## 6. 常用提示模板

小步实现：

```text
使用 incremental-implementation 和 test-driven-development 完成这个功能。
要求：先读当前代码路径，拆成小步；每步只改必要文件；每步说明验证命令和结果。
```

代码审查：

```text
使用 code-review-and-quality 审查当前改动。
优先输出 bug、回归风险、缺失测试和安全问题；没有问题就明确说没有发现阻塞项。
```

接口设计：

```text
使用 api-and-interface-design 设计这个接口。
请给出请求/响应结构、错误语义、兼容性边界、测试点和未来迁移风险。
```

疑难排错：

```text
使用 debugging-and-error-recovery 排查这个错误。
先复现，再定位最小根因，最后给出修复和防回归测试。
```

上线检查：

```text
使用 shipping-and-launch 做上线前检查。
请覆盖配置、迁移、监控、回滚、验证命令和发布后观察点。
```

## 7. 使用边界

- 不要一次性要求加载全部 22 个 skill，容易稀释上下文。
- 不要把 `code-review-and-quality` 当成“润色总结”，它应该优先找问题。
- 不要把 `spec-driven-development` 跳过成直接编码；它的价值在于先锁定验收标准。
- 不要把 `source-driven-development` 用成凭记忆写法；它要求关键实现依据官方文档。
- 不要把 `documentation-and-adrs` 用来记录显而易见的代码；它主要记录为什么这么做、放弃了什么方案、未来如何维护。

## 8. 本地维护规则

本目录下每个 skill 都以独立子目录存在，核心入口是各自的 `SKILL.md`：

```text
agent-skills-ao/
  test-driven-development/
    SKILL.md
  code-review-and-quality/
    SKILL.md
  incremental-implementation/
    SKILL.md
  ...
```

如果后续修改 skill 的 frontmatter、描述或目录结构，记得重新生成总索引：

```powershell
cd C:\Users\zbh\.agents\skills
.\scripts\Update-SkillsReadme.ps1
```

生成后检查：

```powershell
Select-String -Path .\README.md -Pattern 'addyosmani / agent-skills 工程工作流' -Context 0,30
```

