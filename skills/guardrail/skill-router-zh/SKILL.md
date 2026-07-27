---
name: skill-router-zh
description: '中文 skills 总控路由技能：用于在 C:\Users\zbh\.agents\skills 中按任务领域、阶段、风险和交付物选择最少必要 skill 组合，避免一次性加载全量技能。Use when: 技能路由、选择skill、统筹skills库、该用哪个技能、组合多个skill、开始任务前分流、Codex自如使用skills、优化skills调用。不适用于：直接执行具体专业任务，路由后应切换到对应领域 skill。'
---

# Skills 总控路由
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 目标

先判断任务该走哪条流程，再只加载最少必要的 skill。默认选择 1-3 个，复杂任务最多分阶段追加，不要一次性加载整个 skills 仓库。

详细全仓库手册见：`C:\Users\zbh\.agents\skills\SKILL_ROUTING.zh-CN.md`。

## 路由流程

1. **识别任务领域**
   - 技术知识问答：技术概念、术语、ADR、设计决策、“这是什么”“为什么这样设计”或“小白解释”走 `project-dev-zh` 的知识性问题模式；若主要任务是外部资料收集与来源核验，改走 `info-evidence-chain-zh`。
   - 工程开发：项目理解、编码、调试、测试、review、上线；若涉及复杂工程、多方案实现、架构改造、技术 spike、工程 Gate 或候选实现池，先走 `engineering-skill-flow-zh`。
   - 项目结构 / 文件树：新建项目、目录蓝图、前后端或 `apps/packages` 边界、模块/步骤/实验/产物位置、结构重组与漂移审计走 `project-structure-architect`。
   - 工具使用建议：VS Code 插件、Codex 插件、语言包/依赖、Codex MCP、工具选型和安装边界；优先按“四层工具建议框架”回答。
   - Web 设计 / Vibe Coding / 页面改版：网站、Landing Page、Portfolio、产品页、image-to-code、页面高级感、页面太丑、生成 `DESIGN.md` 时先走 `web-design-workflow-zh`；纯局部组件交互或 UI bug 再走 `frontend-ui-engineering`。
   - 参考驱动设计：Web/PPT/Dashboard/科研图/架构图/Coding Prompt 或 Agent 指令需要动态外部案例时，在领域工作流的设计前节点条件加载 `contextual-reference-router`；它不是领域主入口。
   - 科研实验：算法实验、smoke/formal、结果审计、论文 claim 边界；若涉及机制创新、新方法构思、算法创新点、科研调用流、多痛点、多假设、多创新点、候选池或 Gap Gate，先走 `research-skill-flow-zh`，不得直接跳到 `research-coach-zh` 编机制。
   - 写作翻译：论文、翻译、报告文字。
   - 课程任务：考试、实验、实验报告。
   - 调研证据：资料收集、来源核验、证据链。
   - 汇报软著：完整 PPT、路演、答辩、PPTX 生成/修改/模板编辑/渲染验收先走 `ppt-workflow-orchestrator-zh`；只要故事线时走 `ppt-story-design-zh`；真实项目准备度、申请字段、用户手册、源码鉴别材料和已有软著材料审计走 `software-copyright-zh`。
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

## 统一硬门槛模板

当任务命中高风险信号时，不能只说“会注意”，必须在进入编码、实验、论文 claim、子代理调度、正式交付或格式覆盖前，输出或写入阶段记录：

```text
硬门槛：
- 触发门槛：本轮为什么必须先过 gate。
- 前置证据：已读取的文件、模板、文献、raw 结果、测试、截图、日志或用户计划。
- 禁止越界：证据不足时不能声称什么、不能修改什么、不能启动什么。
- 判定结果：PASS / CAUTION / BLOCK。
- 下一步动作：放行、补证据、降级、暂停询问、只做审计或回滚。
```

判定含义：

- PASS：证据足够，允许进入下一阶段，但仍按对应 skill 的验证要求执行。
- CAUTION：可做低风险下一步，但必须降级表述、缩小范围或先补验证；不能升级为正式 claim 或最终交付。
- BLOCK：不得继续执行该高风险动作；只能补证据、改方案、询问用户或记录为失败/待办。

必须使用硬门槛模板的典型场景：

- 论文/报告 claim、formal 结果、冻结版本、算法胜负判断。
- 科研机制创新、新方法、novelty、gap、SOTA 或贡献点判断。
- 复杂工程进入 Main Build、跨模块架构改造、多候选方案收敛。
- Web 正式产品进入整站实现、上线、视觉方向大改或真实浏览器验收。
- 用户给定固定计划、题面、模板、输出结构或禁止自我发挥。
- 子代理真实调度、worker 写文件、外部工具执行会改变本地状态。
- 文件覆盖、批量移动、格式修正覆盖原稿等不可轻易回滚操作。

## 默认组合

### 普通代码改动

```text
incremental-implementation
test-driven-development
code-review-and-quality
```

### 项目结构 / 文件树

```text
project-structure-architect
```

默认执行方式：读取结构证据 -> 检测项目类型与技术栈 -> 选择一个主蓝图 -> dry-run -> 生成或路由文件 -> 更新结构文档 -> audit。已有一致惯例优先；不得为了套模板批量移动文件。纯内容编辑且路径已唯一确定时，不重复调用。

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

知识性解释不涉及代码修改时只加载 `project-dev-zh`。回答开头先用一个具体类比和贯穿实例建立直觉，再用“状态如何变化”组成主链；每条箭头必须说明真实的因果、约束或输入输出关系。指标作为对应状态的证据，并行条件必须说明共同目标及独立共需、相互耦合或互为替代关系，不得强行串成直线。局部例子要明确回扣主链节点，解决动作要反向对应问题状态并给出验收证据。删除节点测试只用于状态主链；全文不更换实例，术语只在对应节点首次解释。

### Web 设计 / Vibe Coding / 页面改版

```text
web-design-workflow-zh
frontend-ui-engineering
browser-testing-with-devtools
```

默认执行方式：先判断快速原型或正式产品，再按新建、现有改版、图像先行选择分支；`DESIGN.md` 通过审美门后先实现纵向切片，再扩展、工程化和浏览器验收。局部 UI bug 不强行重建全站设计。

### 参考驱动设计 / 外部案例路由

```text
领域主工作流
contextual-reference-router（设计前阶段性辅助）
```

默认执行方式：先由领域主工作流锁定任务、受众、行业、技术栈和不可改变项，再用 `contextual-reference-router` 选择 2–5 个来源、打开具体案例、形成 Reference Brief，之后退出并回到领域实现。普通 Bug、纯算法、非设计编码、用户禁止联网、或已有完整参考图且只做严格局部修改时不触发。

### 复杂工程 / 多方案实现调用流

```text
engineering-skill-flow-zh
```

默认执行方式：先做 Project Intake、Solution Gate 和候选实现池；进入 Main Build 前收敛到一个主实现路径或明确组合路径；每阶段最多 2 个辅助 skill，审计/验证 skill 只在触发条件满足时调用。

### 科研多候选探索 / 调用流

```text
research-skill-flow-zh
```

默认执行方式：先做 Memory Intake、文献检索门、Gap Gate 和候选池，再按阶段切换到唯一主 skill；每阶段最多 2 个辅助 skill，审计 skill 只在触发条件满足时调用。凡是机制创新、新方法、算法创新点、novelty、gap、贡献点判断，必须先完成文献/证据链检索并给出“已检索/不可检索/用户禁止检索”的状态，不能凭直觉进入机制设计或编码。

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

### 工具使用建议

```text
skill-router-zh
context-engineering
source-driven-development
```

默认执行方式：按四层回答工具建议：VS Code 插件（编辑器侧能力）、Codex 插件（Codex 内能力和 skill/plugin）、语言本身安装包/生态依赖（运行时、库、CLI、包管理器）、Codex MCP（外部服务、账号、数据源和自动化连接）。逐层说明适用场景、当前是否可用或需要安装、配置位置、验证方式和优先级；不要把 MCP、编辑器插件、Codex 插件和语言包混成一类。

### PPT/软著

按实际任务选择唯一主入口，不要同时加载无关技能。

```text
完整 PPT 闭环：ppt-workflow-orchestrator-zh
仅大纲/故事线：ppt-story-design-zh
软著：software-copyright-zh
```

PPT 总控按阶段动态加载：证据阶段 `info-evidence-chain-zh`，叙事阶段 `ppt-story-design-zh`，视觉阶段 `ppt-visual-system-zh`，从零构建 `pptx-builder-zh`，模板/已有文件编辑 `pptx-template-editor-zh`，数据页 `ppt-data-storytelling-zh`，演讲备注与时间 `ppt-speaker-delivery-zh`，本地成对优秀/反例使用 `ppt-reference-library-zh`，动态外部案例使用 `contextual-reference-router`，长期回归 `pptx-ci-zh`，最终验收 `ppt-render-qa-zh`。两个参考 Skill 默认按缺口二选一，只有维度互补时才同时加载。每阶段只允许 1 个主 Skill、最多 2 个辅助 Skill；首次生成不得交付，必须至少完成一轮修复复验。用户要求全量实现参考计划时，P0、P1、示例与验证必须全部进入覆盖矩阵，任何一项缺实现/测试/证据即为 `BLOCK`。

软著按任务状态路由，不再把“从零开发项目”和“从已有项目生成申请材料”混为默认链路：

```text
已有项目生成材料 / 已有材料审计 / 准备度审计
→ software-copyright-zh

从零开发真实项目
→ project-structure-architect
→ engineering-skill-flow-zh
→ software-copyright-zh

严格按用户材料生成
→ plan-faithful-execution-zh
→ software-copyright-zh

真实浏览器截图
→ browser-testing-with-devtools
→ software-copyright-zh

最终产物整理
→ artifact-curator-zh
```

软著材料必须来自真实项目证据和用户确认；当前登记页面未核验、截图缺失、源码哈希不一致或 DOCX 未完成真实渲染时，最终状态不能是 `PASS`。

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

项目结构门禁横跨 Define、Plan、Build 与 Verify：任何领域工作流一旦要创建或改变持久化文件树，必须追加 `project-structure-architect`，并在阶段收口执行结构审计。

## 不要这样用

- 不要把所有 skill 都加载进上下文。
- 不要只按 skill 名字猜，优先读 `skills/README.md` 的场景分组和触发词。
- 不要用工程 review skill 替代科研结果审计。
- 不要用论文写作 skill 编造实验结果。
- 不要把工程总控流当成普通小修入口；单文件小改、明确 bug fix 或直接代码解释仍走轻量工程 skill。
- 不要回答工具建议时只给单一工具名；必须从 VS Code 插件、Codex 插件、语言本身安装包/生态依赖、Codex MCP 四层拆开边界。
- 不要在科研机制创新、新方法构思或算法创新点任务中跳过文献检索门；没有文献证据只能输出“待检索假设”，不得输出 novelty 或贡献 claim。
- 不要把“深入分析”自动等同于授权子代理；只有用户明确要求 subagent、`/sub`、并行委派或多代理时才真实调度。
- 不要在参考计划不完整时自行扩展关键参数、结论或文件结构。
- 不要把硬门槛模板写成空话；必须给出触发门槛、前置证据、禁止越界、PASS/CAUTION/BLOCK 和下一步动作。

## 输出格式

开始执行前，用 2-4 行给出：

```text
Skill 路由：
- 主 skill：...
- 辅助 skill：...
- 不加载：...，原因是...
```

若命中高风险信号，紧接着输出“硬门槛”五项；若未命中，直接执行即可。

随后按被选中的具体 skill 执行，而不是停留在路由说明。
