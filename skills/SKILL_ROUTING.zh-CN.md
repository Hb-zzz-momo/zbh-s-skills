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

每次任务只选择必要组合：**1 个主 skill + 0-2 个辅助 skill + 必要验证/审计**。

不要一次性加载全部技能。若任务跨领域，分阶段切换 skill。

## 2. 路由四步法

### Step 1：判定领域

| 领域 | 典型任务 | 首选 skill |
|---|---|---|
| 技术知识问答 | 技术概念、术语、ADR、设计决策、为什么这样设计、小白解释 | `project-dev-zh` |
| 工程开发 | 读代码、改代码、接口、调试、测试、review | `project-dev-zh`, `engineering-skill-flow-zh`, `agent-skills-ao/*` |
| GitHub PR CI | GitHub Actions 检查失败、PR checks、Actions 日志定位与修复计划 | `github:gh-fix-ci` |
| 项目结构 / 文件树 | 新建项目、目录蓝图、前后端或 apps/packages 边界、模块/步骤/实验/产物位置、结构重组与漂移审计 | `project-structure-architect` |
| 工具使用建议 | VS Code 插件、Codex 插件、语言包/依赖、Codex MCP、工具选型和安装边界 | `skill-router-zh`, `context-engineering`, `source-driven-development` |
| Web 设计 / Vibe Coding / 页面改版 | 网站、Landing Page、Portfolio、产品页、image-to-code、页面高级感、页面太丑、生成 DESIGN.md | `web-design-workflow-zh` |
| 参考驱动设计 | Web/PPT/Dashboard/科研图/架构图/Coding Prompt 或 Agent 指令需要动态外部案例、行业标杆与设计转译 | `contextual-reference-router`（领域工作流的阶段性辅助） |
| 严格计划执行 | 按题面、方案、计划、prompt 文件执行 | `plan-faithful-execution-zh` |
| 子代理调度 | `/sub`、subagents、子代理、多代理、并行委派、worker/explorer | `subagent-orchestration-zh` |
| 科研调用流 | 机制创新、新方法构思、算法创新点、多痛点、多假设、多创新点、候选池、文献检索门、Gap Gate、科研 skill 路由 | `research-skill-flow-zh` |
| 工程调用流 | 复杂工程、多方案实现、技术 spike、工程 Gate、候选实现池 | `engineering-skill-flow-zh` |
| 科研实验 | 算法实验、smoke/formal、消融、结果收口 | `research-experiment-ops-zh` |
| 决定性审计 | formal/gate、论文主表、是否支撑 claim | `decisive-result-audit-zh` |
| 科研迭代复盘 | 判断是不是越改越差、机制是否可写 | `research-iteration-audit-zh` |
| 论文写作 | 摘要、引言、方法、实验、结论、润色 | `paper-writing-zh` |
| 论文格式修正 | Word论文排版、毕业论文格式、期刊模板、docx格式检查、图表题注、页边距、标题样式、参考文献格式统一 | `paper-format-fixer-zh` |
| 翻译 | 英文学术/技术文本英译中 | `translation-zh` |
| 课程考试 | 选择题、简答题、计算题、作业 | `exam-answer-zh` |
| 课程实验 | 实验排错、截图规划、实验报告 | `lab-report-coach-zh` |
| 信息调研 | 查资料、证据链、来源核验 | `info-evidence-chain-zh` |
| PPT 汇报 | 路演、课程汇报、答辩、生成或修改可编辑 PPTX、模板编辑、渲染验收 | `ppt-workflow-orchestrator-zh` |
| 软著 | 真实项目准备度、申请字段、用户手册、真实截图、源码鉴别材料、已有材料审计与提交前校验 | `software-copyright-zh` |
| 长任务 | 后台任务、轮询、卡死恢复、manifest | `agent-wait-monitor-zh` |
| 产物整理 | skill-outputs、日志、旧产物归档 | `artifact-curator-zh` |
| 工作流沉淀 | SOP、流程优化、新 skill 工作流 | `workflow-forge-zh` |
| 学习复盘 | 任务结束后总结知识点 | `knowledge-digest-zh` |

### Step 2：判定阶段

| 阶段 | 目标 | 工程 skill |
|---|---|---|
| Define | 想清楚做什么、为什么做、验收什么 | `interview-me`, `idea-refine`, `spec-driven-development` |
| Plan | 拆任务、排顺序、设检查点 | `planning-and-task-breakdown` |
| Build | 小步实现、少量改动、持续验证 | `incremental-implementation` |
| Verify | 测试、浏览器验证、复现问题、PR Actions 失败定位、生产可诊断性 | `test-driven-development`, `browser-testing-with-devtools`, `debugging-and-error-recovery`, `github:gh-fix-ci`, `observability-and-instrumentation` |
| Review | 代码质量、安全、性能、简化 | `code-review-and-quality`, `security-and-hardening`, `performance-optimization`, `code-simplification` |
| Ship | Git、CI/CD、文档、上线、回滚 | `git-workflow-and-versioning`, `ci-cd-and-automation`, `documentation-and-adrs`, `shipping-and-launch` |

### Step 3：判定风险

| 风险信号 | 追加 skill |
|---|---|
| 用户给了固定计划、题面或边界 | `plan-faithful-execution-zh` |
| 任务将初始化或重组项目，或新增/移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树 | `project-structure-architect` |
| 科研机制创新、新方法构思、算法创新点、novelty 或 gap 判断 | `research-skill-flow-zh`, `info-evidence-chain-zh` |
| 结论会写进论文或报告 | `decisive-result-audit-zh`, `paper-writing-zh` |
| 改动涉及认证、权限、输入、密钥 | `security-and-hardening` |
| 页面必须真实可用或需要视觉设计验收 | `web-design-workflow-zh`, `frontend-ui-engineering`, `browser-testing-with-devtools` |
| 设计、展示、图表或提示系统需要动态外部案例 | 在对应领域工作流的设计前节点追加 `contextual-reference-router` |
| 性能是目标或存在回归 | `performance-optimization` |
| 任务会长时间运行 | `agent-wait-monitor-zh` |
| 用户明确要求 subagent、`/sub`、并行委派或多代理 | `subagent-orchestration-zh` |
| 需要沉淀给下一任 AI | `project-handoff-zh`, `documentation-and-adrs` |

### 高风险任务统一硬门槛模板

凡 Step 3 命中风险信号，或任务会进入编码、实验、论文 claim、子代理调度、正式交付、文件覆盖、批量移动等不可轻易回滚动作前，必须先输出或写入阶段记录：

```text
硬门槛：
- 触发门槛：本轮为什么必须先过 gate。
- 前置证据：已读取的文件、模板、文献、raw 结果、测试、截图、日志或用户计划。
- 禁止越界：证据不足时不能声称什么、不能修改什么、不能启动什么。
- 判定结果：PASS / CAUTION / BLOCK。
- 下一步动作：放行、补证据、降级、暂停询问、只做审计或回滚。
```

判定规则：

- `PASS`：证据足够，允许进入下一阶段，但仍要执行对应 skill 的验证要求。
- `CAUTION`：只允许低风险下一步，必须降级表述、缩小范围或补验证；不得升级为正式 claim 或最终交付。
- `BLOCK`：不得继续该高风险动作，只能补证据、改方案、询问用户或记录为失败/待办。

### Step 4：声明并执行

执行前只需用 2-4 行说明：主 skill 是哪个、为什么选它、辅助 skill 用来做什么、哪些明显不加载。用普通列表写，不要包成代码块。

若命中高风险信号，声明路由后先给出“硬门槛”五项；未命中时直接工作，不要把路由变成长篇计划。

## 3. 常见任务组合

### 技术知识问答

`project-dev-zh`

默认执行方式：若绑定项目先读取证据；先给结论，再用一个具体类比和贯穿实例建立直觉，然后按因果讲清为什么。每条箭头必须有真实的因果、约束或输入输出关系，补不出理由就改成并列或删掉；指标挂到对应判断下作为证据，并行条件说明共同目标及彼此关系，不得强行线性化。全文不更换实例，术语只在首次出现的位置解释；只有用户本身在排查故障时，才改用“现状 → 症状 → 根因 → 修复动作 → 验收证据”。

### 代码修改

`project-dev-zh`、`incremental-implementation`、`test-driven-development`、`code-review-and-quality`

默认执行方式：读现有代码 -> 小步修改 -> 跑测试/检查 -> review 风险。

### 项目结构 / 文件树

`project-structure-architect`

默认执行方式：读取现有结构证据 -> 检测项目类型与技术栈 -> 选择一个主蓝图 -> dry-run -> 生成或路由文件 -> 更新结构文档 -> audit。已有一致惯例优先；不因偏好模板批量移动文件。纯内容编辑且路径已唯一确定时，不重复调用。

### 代码库架构深化

`improve-codebase-architecture`、`codebase-design`

默认执行方式：先按近期热点、领域词汇和 ADR 扫描浅模块，生成候选报告；用户选定候选后再用 `grilling` 澄清决策，并在术语或决策确实变化时追加 `domain-modeling`。未获用户明确授权时由主代理本地探索，不调度子代理。

### 复杂工程 / 多方案实现

`engineering-skill-flow-zh`

默认执行方式：Project Intake -> Solution Gate -> Implementation Design -> Candidate Spike / Slice Funnel -> Main Build -> Verify / Review -> Ship / Memory。进入 Main Build 前必须收敛到一个主实现路径或明确组合路径；普通小改不走这个总控流。

### 有明确参考计划的工程任务

`plan-faithful-execution-zh`、`incremental-implementation`、`test-driven-development`

默认执行方式：先锁定计划边界；缺口先问；禁止擅自扩大参数、目标、文件结构和结论。

### 子代理 / 多代理委派

`subagent-orchestration-zh`

默认执行方式：只有用户明确授权 subagent、`/sub`、并行代理、委派、worker/explorer 时才真实调度。父代理保留本地主 skill、写范围、最终集成和验收；子代理默认使用只读 explorer/reviewer。当父代理明确给出最小任务、唯一写范围、禁止越界规则、验证命令和回收门槛时，可以使用 worker 修改文件，且 worker 改动必须由父代理复核、集成、测试和最终验收。

### Web 设计 / Vibe Coding / 前端页面

`web-design-workflow-zh`、`frontend-ui-engineering`、`browser-testing-with-devtools`

默认执行方式：先判断快速原型或正式产品，再按新建、现有改版、图像先行选择分支；需要动态外部案例时，在需求锁定后、`DESIGN.md` 前阶段性调用 `contextual-reference-router` 形成 Reference Brief；生成/修订 `DESIGN.md` 后先做纵向切片，再工程实现和浏览器验收。纯局部组件交互或 UI bug 可直接走 `frontend-ui-engineering`。

### 参考驱动设计

领域主工作流，加 `contextual-reference-router`（只在参考阶段加载）。

默认执行方式：领域工作流先锁定交付物、受众、行业、技术栈和不可改变项；Router 再选择 2–5 个互补来源、打开具体案例、形成 Reference Brief，并在进入实现前退出。它不替代事实证据、官方技术文档、设计契约、工程测试或最终视觉验收。普通 Bug、纯算法、用户禁止联网或严格按完整参考图做局部修改时不触发。

### API / 模块边界

`api-and-interface-design`、`test-driven-development`、`documentation-and-adrs`

默认执行方式：先定义契约、错误语义、兼容边界，再实现和测试。

### Bug 排查

`debugging-and-error-recovery`、`test-driven-development`、`code-review-and-quality`

默认执行方式：复现 -> 定位最小根因 -> 修复 -> 加回归测试 -> review。

### GitHub PR CI 失败

`github:gh-fix-ci`

默认执行方式：`gh auth status` -> 解析 PR checks -> 获取 GitHub Actions 日志 -> 总结根因和失败证据 -> 提出聚焦修复计划 -> 用户批准后修改与本地复验。非 GitHub Actions 检查只报告链接；新建或修改流水线改走 `ci-cd-and-automation`。

### 科研多候选探索 / 调用流

`research-skill-flow-zh`、`info-evidence-chain-zh`

默认执行方式：Memory Intake -> 文献检索门 -> Gap Gate -> Research Design -> Candidate Smoke Funnel -> Dev/Formal -> Paper Memory。凡是机制创新、新方法构思、算法创新点、novelty 或 gap 判断，必须先用 `info-evidence-chain-zh` 或等价文献检索产出证据链；未检索只能输出“待检索假设”，不得进入机制设计、编码或论文贡献 claim。每阶段只允许 1 个主 skill、最多 2 个辅助 skill；审计 skill 只在触发条件满足时调用。

### 科研实验

`research-experiment-ops-zh`、`agent-wait-monitor-zh`、`artifact-curator-zh`

默认执行方式：smoke/dev/formal 分阶段；检查 raw、summary、metric、seed、配置一致性；固定计划触发 `plan-faithful-execution-zh`，formal、冻结版本或论文 claim 触发 `decisive-result-audit-zh`。

### 论文写作

`paper-writing-zh`、`research-coach-zh`、`research-statistics-reporting-zh`

默认执行方式：材料驱动写作；事实、推理、建议分开；实验结论必须被结果支撑；正式 claim 触发 `decisive-result-audit-zh`。

### 论文格式修正

`paper-format-fixer-zh`、`paper-writing-zh`

默认执行方式：优先读取用户给的学校/期刊格式要求、样例 `.docx` 或模板文件；先审计 `.docx` 页面、样式、段落、表格、图表题注和参考文献格式，再保守修正并输出新文件。内容写作仍交给 `paper-writing-zh`，不要把格式修正扩展成论文 claim 或实验结论改写。

### 信息调研

`info-evidence-chain-zh`、`source-driven-development`

默认执行方式：查来源、分级证据、保留链接、标注时效和不确定性。

### 工具使用建议

`skill-router-zh`、`context-engineering`、`source-driven-development`

默认执行方式：当用户询问工具怎么选、怎么装、怎么接入、某能力该放在哪一层时，按四层回答：VS Code 插件（编辑器侧能力）、Codex 插件（Codex 内能力和 skill/plugin）、语言本身安装包/生态依赖（运行时、库、CLI、包管理器）、Codex MCP（外部服务、账号、数据源和自动化连接）。每层说明适用场景、当前是否可用或需要安装、配置位置、验证方式和优先级；不要把 MCP、编辑器插件、Codex 插件和语言包混成一类。

### 汇报 / PPT

`ppt-workflow-orchestrator-zh`

默认执行方式：材料读取 -> 分支判断 -> 证据链 -> 叙事与 Slide Contract -> PRESENTATION_DESIGN.md -> 三页纵向切片 -> 构建或模板编辑 -> 全量渲染 -> QA -> 至少一轮修复复验 -> 交付。动态外部案例按需使用 `contextual-reference-router`，本地成对优秀/反例使用 `ppt-reference-library-zh`，默认按缺口二选一；演讲备注追加 `ppt-speaker-delivery-zh`，长期回归使用 `pptx-ci-zh`。每阶段仅 1 个主 Skill，最多 2 个辅助 Skill，不一次加载全部 PPT Skills；全量实现请求必须覆盖计划中的 P0、P1、示例与验证。

按任务形态选择最小组合：

- 仅规划：`ppt-story-design-zh` + `info-evidence-chain-zh`
- 从零生成：`pptx-builder-zh` + `ppt-render-qa-zh`
- 模板/已有文件编辑：`pptx-template-editor-zh` + `ppt-render-qa-zh`
- 数据型汇报：`ppt-data-storytelling-zh` + `ppt-render-qa-zh`
- 视觉系统：`ppt-visual-system-zh`（只在 Visual System 阶段加载）

### 软著

`software-copyright-zh`

默认执行方式：任务模式识别 -> 唯一项目定位 -> 环境与准备度 -> 真实证据链 -> 业务理解确认 -> 申请字段确认 -> 源码候选与用户确认 -> 真实截图 -> Markdown 草稿整体确认 -> 正式 DOCX/TXT -> 一致性、来源与渲染校验 -> 最终清单。未实现功能、第三方源码、AI 生成截图和未经确认的事实不得进入正式材料。

按阶段选择最小路由：

```text
已有项目生成材料 / 已有材料审计 / 准备度审计
→ software-copyright-zh

从零开发用于申报的真实项目
→ project-structure-architect
→ engineering-skill-flow-zh
→ software-copyright-zh

严格按用户提供材料生成
→ plan-faithful-execution-zh
→ software-copyright-zh

真实浏览器截图
→ browser-testing-with-devtools
→ software-copyright-zh

最终产物整理
→ artifact-curator-zh
```

每个阶段只加载 1 个主 Skill 和最多 2 个辅助 Skill。`software-copyright-zh` 不单独承担普通项目开发；当前登记页面未核验、截图缺失或 DOCX 未完成真实渲染时，不得宣称材料可直接提交。

### 长时间实验或后台任务

`agent-wait-monitor-zh`、`artifact-curator-zh`

默认执行方式：后台启动、进度文件、日志轮询、卡死判断、结果归档。

## 4. 默认守门规则

以下规则优先级高于具体 skill 的便利性：

- 有参考计划时，先用 `plan-faithful-execution-zh` 锁边界。
- 任何工作流将创建或改变项目文件树时，先用 `project-structure-architect` 做搭建前检测、运行期路径路由和阶段收口审计。
- 复杂工程、多方案实现或架构改造先用 `engineering-skill-flow-zh` 建候选池和 Gate；单文件小改仍直接走轻量工程 skill。
- 有代码行为变化时，默认加入测试或可执行验证。
- 有论文/报告结论时，默认做证据和结果审计。
- 有科研机制创新、新方法或算法创新点时，默认先做文献检索门；不得从本地实验直觉直接生成 novelty claim。
- 命中高风险信号时，必须使用统一硬门槛模板；没有前置证据只能 `CAUTION` 或 `BLOCK`，不能写成 `PASS`。
- 有子代理请求时，先确认授权和写范围；不要把“深入分析”自动当作授权。
- 有工具使用建议请求时，按 VS Code 插件、Codex 插件、语言本身安装包/生态依赖、Codex MCP 四层组织答案，并区分“已安装可用”“需要配置”“只是候选建议”。
- 有用户指定输出目录时，写入指定目录。
- 不确定时先查 `skills/README.md`，再选择 skill。
- 一次最多主动加载 1-3 个 skill；复杂任务分阶段追加。

## 5. 给 Codex 的固定提示

可以在任务开头直接说：`先用 skill-router-zh 做技能路由，只选择必要的 1-3 个 skill，然后直接执行。`

或者：`这次任务按 skills/SKILL_ROUTING.zh-CN.md 统筹，不要全量加载 skills。`

如果任务是工程类：`按 agent-skills-ao 的 Define -> Plan -> Build -> Verify -> Review -> Ship 生命周期判断阶段，再调用对应 skill。`

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
