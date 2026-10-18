# contextual-reference-router 全量覆盖矩阵

依据：`skill生成工作流/参考网站路由skill.md`、根级 `AGENTS.md`、`skill-creator/SKILL.md`。

| 计划要求 | 实现 | 测试 | 交付证据 | 状态 |
|---|---|---|---|---|
| 创建名为 `contextual-reference-router` 的标准 Skill | 使用 `init_skill.py` 初始化，生成 `SKILL.md` 与 `agents/openai.yaml` | `quick_validate.py` 返回 `Skill is valid!` | `skills/guardrail/contextual-reference-router/` | PASS |
| 不是网站收藏夹，而是上下文参考决策系统 | 主流程覆盖任务理解、维度识别、来源路由、具体案例、分析表、多来源综合、设计转译、执行、自检 | 路由回归 + 两次真实前向测试 | `SKILL.md`、PPT/Dashboard Reference Brief | PASS |
| 明确触发与排除场景 | description 覆盖 Web/UI、Dashboard、PPT、Prompt、数据可视化、科研/架构图、视觉资产及排除项 | 计划 7 例 + Landing/App/PPT visual/色彩/字体/Agent rules/视觉资产/报告模板/禁止联网/严格局部修改/Dashboard Bug 等扩展回归 | frontmatter、`tests/test_reference_router.py` | PASS |
| 主 Skill 紧凑并渐进加载 | `SKILL.md` 只保留核心规则，详细清单进入 references | frontmatter、行数与 5 个引用文件自动校验 | `SKILL.md`、5 个 references | PASS |
| 完整来源注册表 | 36 个计划来源分别记录名称、域名、主要用途、适用任务、优点、局限、关键词、案例要求、注意事项 | 来源全集与六组独立字段表头校验 | `references/source-registry.md` | PASS |
| 完整任务路由矩阵 | 覆盖计划 15 类并扩展视觉资产、报告模板；辅助脚本不替代语义判断 | 计划路由、扩展类别和边界回归 | `references/routing-matrix.md`、`scripts/reference_router.py` | PASS |
| 定向搜索与数量控制 | 2–5 网站、3–8 案例、2–4 核心来源、3–7 规律；上下文关键词公式与停止条件 | route 输出边界 + Brief 数量口径回归 | `references/search-playbook.md`、验证脚本 | PASS |
| 参考证据与 Reference Brief | 每案例记录 URL/路径、相关性、事实、观察、推断、采用、放弃、转译、许可证/限制 | 正常、伪 URL、首页、字段缺失、数量错位和失败退出码测试 | `references/reference-analysis-template.md`、验证脚本 | PASS |
| 参考落实自检 | 覆盖任务适配、案例访问、多来源、可执行规律、转化、品牌、许可、限制、事实/观察/推断 | Brief Gate 正常与失败路径 | `references/quality-checklist.md`、前向自检 | PASS |
| 联网失败和网站降级 | 明示实时检索限制、要求本地可靠材料与落实记录，不虚构访问，状态最高 `CAUTION` | 空壳离线 `BLOCK`、完整离线 `CAUTION` | `SKILL.md`、search playbook、validator tests | PASS |
| 输出简洁“参考依据” | 固定 Reference Brief、最终反馈与阶段限定状态 | schema 验证 + 两次真实 Brief | 模板、`forward-test/`、`fresh-agent-forward-test/` | PASS |
| 脚本增加必须有稳定性价值 | 仅增加确定性路由、Brief Gate、批量验收；所有核心决策仍要求语义判断与真实案例 | CLI 正常/失败路径、28 项单测 | `scripts/reference_router.py` | PASS |
| 接入 Web 工作流 | 在需求规格化后、`DESIGN.md` 前调用本 Skill | 节点顺序与跳过条件测试 | `web-design-workflow-zh/SKILL.md` | PASS |
| 接入 PPT 工作流 | Evidence 后、Narrative/Visual System 前增加条件检查点，不新增未同步状态机阶段 | 集成标记与边界测试 | `ppt-workflow-orchestrator-zh/SKILL.md` | PASS |
| 接入科研图/架构图工作流 | 科学事实锁定后、生成策略与 brief 前调用 | 节点顺序、事实边界与 BioRender 双重身份测试 | `research-figure-generation-zh/SKILL.md` | PASS |
| 接入 Coding Prompt/Agent 工作流 | Project Intake 后、Solution Gate 前条件调用，并在总路由注册 | 集成标记、全仓手册与 agent-rules CLI 回归 | `engineering-skill-flow-zh`、`skill-router-zh`、路由手册 | PASS |
| 接入工作流生成/优化 | 按模式 A/B/C/D 在不篡改原始经验的前提下条件调用 | 四模式集成测试 | `workflow-forge-zh/SKILL.md` | PASS |
| 运行计划给出的 7 个验收任务 | Web 视觉、Web 流程、PPT、Coding Prompt、Dashboard、科研机制图、不应触发 | `batch-test` 7/7，失败 0；全量单测 28/28 | `tests/`、`test-report.json` | PASS |
| 实际执行 Skill | 主代理执行 PPT 路由与 Brief；全新代理独立执行 Dashboard，打开 4 站 7 个具体案例并自检 | validator `PASS` + 主代理独立复核 `PASS` | `forward-test/`、`fresh-agent-forward-test/`、复核报告 | PASS |
| 更新技能注册表 | 增加 `Use when:` 与 guardrail 场景映射，运行标准生成器 | README 描述、触发词和分类自动测试 | `skills/README.md`、`Update-SkillsReadme.ps1` | PASS |
| 最终反少实现审计 | 检查遗漏、错实现、仅文档、仅 smoke、不可复现、未授权假设 | 独立代理审计 + 主代理复核 | `anti-underimplementation-audit.md` | PASS |

整体状态：`PASS`。所有计划必选项均有实现、测试和可核查交付证据；真实前向测试的 `PASS` 仅限 Reference Brief 阶段，不代表下游 PPT 或 Dashboard 已构建。
