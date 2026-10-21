# 按领域读取的路由细则

仅在命中对应领域或高风险门槛时读相关小节，不默认全文加载。本文件保留原有专用规则；总调度与方案B触发以主文件为准。

## 统一硬门槛模板

需要执行或制品验收的任务，完成声明前读取[执行输出与完成声明规则](../../../course/course-lab-workflow-zh/references/verification-completion.md)：完整输出中的未分类诊断阻断完成声明，仍存在的非阻断警告明示为CAUTION；运行、正确性、必要视觉和最终包分别判定，不能只凭退出码或零异常放行。

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
- CAUTION：可继续已授权的低风险工作并交付明确限制的产物，但必须降级表述、缩小范围或先补验证；不能升级为总体PASS、无问题或可直接提交的声明。
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

`incremental-implementation`、`test-driven-development`、`code-review-and-quality`

### GitHub PR CI 失败

`github:gh-fix-ci`

默认执行方式：先确认 `gh auth status`，再读取 PR checks 与 Actions 日志并总结根因；外部 CI 只报告链接。提出聚焦修复计划并等待用户批准后，才修改代码和复验。

### 项目结构 / 文件树

`project-structure-architect`

默认执行方式：读取结构证据 -> 检测项目类型与技术栈 -> 选择一个主蓝图 -> dry-run -> 生成或路由文件 -> 更新结构文档 -> audit。已有一致惯例优先；不得为了套模板批量移动文件。纯内容编辑且路径已唯一确定时，不重复调用。

### 代码库架构深化

`improve-codebase-architecture`、`codebase-design`

默认执行方式：先按近期热点、领域词汇和 ADR 扫描浅模块，生成候选报告；用户选定候选后再用 `grilling` 澄清决策，并在术语或决策确实变化时追加 `domain-modeling`。既无本次明确授权又未命中独立评价持续授权时，由主代理本地探索，不调度子代理。

### 有参考计划或用户强调不要自作主张

`plan-faithful-execution-zh`、`incremental-implementation`、`code-review-and-quality`

### 子代理 / 多代理委派

`subagent-orchestration-zh`

默认执行方式：确认本次明确授权或适用的持续授权；质量评价、候选比较和交付验收已持续授权，先接入 `multi-agent-evaluation-zh`。其他未授权调度只给本地方案。父代理保留主 skill、写范围与集成；reviewer 不修改被评对象，worker 只在明确写范围内修改，由父代理集成验证。独立阻断项必须凭证据闭环。

### 中文项目理解和工程开发

`project-dev-zh`、`incremental-implementation`、`test-driven-development`

知识性解释不涉及代码修改时只加载 `project-dev-zh`。回答先给结论，再用一个具体类比和贯穿实例建立直觉，然后按因果讲清为什么。每条箭头必须说明真实的因果、约束或输入输出关系，补不出理由就改成并列或删掉。并行条件要说明共同目标及彼此关系，不得强行串成直线；全文不更换实例，术语只在首次出现的位置解释。只有用户本身在排查故障时，才改用“现状 → 症状 → 根因 → 修复动作 → 验收证据”的顺序。

### Web 设计 / Vibe Coding / 页面改版

`web-design-workflow-zh`、`frontend-ui-engineering`、`browser-testing-with-devtools`

默认执行方式：先判断快速原型或正式产品，再按新建、现有改版、图像先行选择分支；`DESIGN.md` 通过审美门后先实现纵向切片，再扩展、工程化和浏览器验收。局部 UI bug 不强行重建全站设计。

### 参考驱动设计 / 外部案例路由

领域主工作流，加 `contextual-reference-router`（设计前阶段性辅助）。

默认执行方式：先由领域主工作流锁定任务、受众、行业、技术栈和不可改变项，再用 `contextual-reference-router` 选择 2–5 个来源、打开具体案例、形成 Reference Brief，之后退出并回到领域实现。普通 Bug、纯算法、非设计编码、用户禁止联网、或已有完整参考图且只做严格局部修改时不触发。

### 复杂工程 / 多方案实现调用流

`engineering-skill-flow-zh`

默认执行方式：先做 Project Intake、Solution Gate 和候选实现池；进入 Main Build 前收敛到一个主实现路径或明确组合路径；每阶段最多 2 个辅助 skill，审计/验证 skill 只在触发条件满足时调用。

### 科研多候选探索 / 调用流

`research-skill-flow-zh`

默认执行方式：先做 Memory Intake、文献检索门、Gap Gate 和候选池，再按阶段切换到唯一主 skill；每阶段最多 2 个辅助 skill，审计 skill 只在触发条件满足时调用。凡是机制创新、新方法、算法创新点、novelty、gap、贡献点判断，必须先完成文献/证据链检索并给出“已检索/不可检索/用户禁止检索”的状态，不能凭直觉进入机制设计或编码。

### 科研算法实验

`research-experiment-ops-zh`、`agent-wait-monitor-zh`、`artifact-curator-zh`

默认执行方式：smoke/dev/formal 分阶段执行；固定计划时触发 `plan-faithful-execution-zh`，formal、冻结版本或论文 claim 时触发 `decisive-result-audit-zh`。

### 新媒体传播内容

黑客松内容优先 `hackathon-content-workflow-zh` 作阶段总控，通用宣传Skill提供事实/编辑能力而非第二主入口。按任务选择推文、手册、重组/校对或局改分支；文档/浏览器/独立评审按阶段调用，既有记忆与反思锚点复用，不循环分流、不强制全部载体。

`publicity-content-workflow-zh`，按载体追加发布/文风/生图 skill。

默认执行方式：先核验并冻结时间、地点、人物、事项、结果等事实，再定内容逻辑、模板、载体适配和版式。关键事实不确定即 `BLOCK`；非关键待确认项必须集中披露。发布前完成合规、真实渲染和独立评价，不能以吸引力或排版优化覆盖事实边界。

### 论文/报告文字

`paper-writing-zh`、`research-coach-zh`、`plan-faithful-execution-zh`

### 信息调研

`info-evidence-chain-zh`、`source-driven-development`

### 工具使用建议

`skill-router-zh`、`context-engineering`、`source-driven-development`

默认执行方式：按四层回答工具建议：VS Code 插件（编辑器侧能力）、Codex 插件（Codex 内能力和 skill/plugin）、语言本身安装包/生态依赖（运行时、库、CLI、包管理器）、Codex MCP（外部服务、账号、数据源和自动化连接）。逐层说明适用场景、当前是否可用或需要安装、配置位置、验证方式和优先级；不要把 MCP、编辑器插件、Codex 插件和语言包混成一类。

### PPT/软著

按实际任务选择唯一主入口，不要同时加载无关技能。

- 完整 PPT 闭环：`ppt-workflow-orchestrator-zh`
- 仅大纲/故事线：`ppt-story-design-zh`
- 软著：`software-copyright-zh`

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

`agent-wait-monitor-zh`、`artifact-curator-zh`

## 工程生命周期映射

| 阶段 | 首选 skill |
|---|---|
| Define | `idea-refine`, `spec-driven-development` |
| Plan | `planning-and-task-breakdown`, `plan-faithful-execution-zh` |
| Build | `incremental-implementation`, `project-dev-zh` |
| Verify | `test-driven-development`, `browser-testing-with-devtools`, `debugging-and-error-recovery`, `github:gh-fix-ci` |
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
- 不要把“深入分析”当作无限委派授权；真实调度依本次明确委派或已持续授权的独立评价范围，本次禁用优先。
- 不要在参考计划不完整时自行扩展关键参数、结论或文件结构。
- 不要把硬门槛模板写成空话；必须给出触发门槛、前置证据、禁止越界、PASS/CAUTION/BLOCK 和下一步动作。
