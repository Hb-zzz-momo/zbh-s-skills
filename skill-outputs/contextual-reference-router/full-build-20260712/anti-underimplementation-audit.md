# 反少实现与自我衍生审计

依据：`skill生成工作流/参考网站路由skill.md`、根级 `AGENTS.md`、`skill-creator` 创建规范与当前稳定实现。

## 最终判定

`PASS`：计划必选项、计划 7 个验收任务、工作流接入、注册表、真实调用和交付验证均已闭环。没有用文档、空目录、占位脚本、伪数据或 smoke 结果冒充全量实现。

## 反少实现检查

| 风险 | 检查结果 | 证据 | 状态 |
|---|---|---|---|
| 漏实现计划阶段 | 十阶段闭环全部进入主 Skill；五份 references 分别承载来源、矩阵、检索、分析模板、质量门 | `SKILL.md`、`references/` | PASS |
| 漏来源或漏字段 | 计划 36 个来源全部存在；名称、域名、主要用途、适用任务、优点、局限、关键词、具体案例要求、注意事项独立记录 | `source-registry.md` + 包级测试 | PASS |
| 路由错实现 | 计划 15 类全部覆盖；图标/插画和报告模板两项扩展同时写入矩阵与脚本，不存在脚本私有规则 | `routing-matrix.md`、17 路由 catalog 测试 | PASS |
| 错误触发/漏触发 | 覆盖计划 7 例和 Landing、后台、高端 PPT、配色、字体、Agent rules、信息层级、UX、视觉资产、报告模板；禁止联网、严格局改、算法、翻译、Dashboard Bug 均不触发 | route tests | PASS |
| 只有网站列表 | Skill 强制任务锁定、具体案例、事实/观察/推断、采用/拒绝、转译、落实和许可证 Gate | 主 Skill、validator、两份真实 Brief | PASS |
| 只有文档没有执行逻辑 | 提供确定性路由、Brief 校验、批量回归 CLI，并验证正常与失败退出码 | `scripts/reference_router.py`、tests | PASS |
| 数量口径混用 | 已检查网站 2–5、案例 3–8、核心参考 2–4、规律 3–7 分字段校验；合法的“看 5 个、留 2 个”能通过 | validator tests | PASS |
| 离线空壳误报 | 离线必须有本地可靠材料、规则、落实、限制与事实分层；完整时最高 `CAUTION`，空壳为 `BLOCK` | offline tests | PASS |
| 只做 smoke | 28 项单元/集成测试、7/7 计划回归、PPT 主代理联网测试、Dashboard 全新代理联网测试 | `validation-report.md` | PASS |
| 不可复现 | Skill 校验、测试、批量路由、Brief Gate 和 README 生成均有固定入口与保存结果 | commands + `test-report.json` | PASS |
| 工作流接错节点 | Web 在规格后/DESIGN 前；PPT 在 Evidence/Narrative/Visual 前；科研图在事实锁定后/策略前；工程在 Intake/Solution Gate 间；workflow-forge 按 A/B/C/D 分支 | 集成测试 + 独立接入审计 | PASS |
| 用扩展替代计划 | 先完成计划 15 类、36 来源和 7 回归，再扩展视觉资产、报告模板、CLI 与额外边界测试 | coverage matrix | PASS |
| 状态越界 | 两次真实调用都只对 Reference Brief 阶段判 `PASS`；PPT 与 Dashboard 本体明确为未授权/N/A | forward-test 产物 | PASS |

## 独立审计发现与修复

独立代理在稳定前审计中实际发现并推动修复：

1. README 无描述且被归到“其他” → 增加 `Use when:` 与 guardrail 场景映射，重生成并测试。
2. Brief Gate 允许离线空壳、伪 URL、无 facts/inferences → 加严 schema、URL、证据和离线 Gate。
3. 把 3–8 案例与 2–4 核心参考混为一谈 → 拆分计数字段并回归合法边界。
4. Landing/后台/高端 PPT/配色/字体等路由粗略合并，UX/图标/报告模板漏触发，Dashboard Bug 误触发 → 扩展并修正路由测试。
5. 脚本扩展未同步矩阵 → 增补报告模板与图标/插画两条矩阵规则。
6. Web/PPT 工作流触发语义偏窄 → Web 补用户流程/信息层级/响应式/UX；PPT 新建或重设计默认进入参考 Gate，并保留两类跳过条件。

所有问题均在最终回归前修复，未把审计建议降级为“后续待办”。

## 自我衍生审计

- 未改变用户指定 Skill 名称、参考来源范围、数量口径、状态体系或最终输出目标。
- 新增脚本只用于稳定路由、校验和回归，符合参考文档“确实提高检索和验收稳定性时可增加”的边界。
- 新增视觉资产和报告模板路由来自计划明确触发项，不是任意扩大领域。
- 工作流只在与 Web、PPT、科研图/架构、Coding Prompt/Agent、工作流生成直接相关的节点接入；未让本 Skill 替代事实证据、官方技术规范、领域实现或最终 QA。
- 没有固化用户未提供的品牌、阈值、权重、技术栈、数据口径或视觉资产许可；真实测试中均作为开放决策或限制保留。
- 未覆盖、重置或删除工作区中与本任务无关的已有改动；未创建提交。

## 阻断项

无。
