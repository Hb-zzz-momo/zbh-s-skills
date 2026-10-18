# contextual-reference-router 验证报告

日期：2026-07-12  
验收范围：Skill 包、确定性辅助脚本、Reference Brief Gate、计划回归、扩展边界、工作流接入、注册表与真实前向调用。

## 自动化结果

| 验证 | 命令/入口 | 结果 |
|---|---|---|
| Skill 结构与 frontmatter | `python -X utf8 .../skill-creator/scripts/quick_validate.py skills/guardrail/contextual-reference-router` | `PASS`，`Skill is valid!` |
| 全量单元/集成测试 | `python -X utf8 -m unittest discover -s skills/guardrail/contextual-reference-router/tests -p test_*.py -v` | `PASS`，28/28 |
| 计划 7 个验收任务 | `reference_router.py batch-test --cases tests/cases.json` | `PASS`，7/7，失败 0 |
| Brief 正常路径 | PPT 前向测试 JSON 经 `validate-brief` | `PASS` |
| Brief 失败路径 | 首页、伪 URL、字段缺失、数量错位、空壳离线、CLI 非零退出 | 均按预期 `BLOCK`；CLI 返回 2 |
| 离线完整降级 | 本地可靠材料 + 明确限制 + 落实记录 | `CAUTION`，不会误报 `PASS` |
| 注册表生成 | `skills/scripts/Update-SkillsReadme.ps1` | 62 个 Skill；本 Skill 位于 guardrail，描述和触发词非空 |

## 回归覆盖

- 计划 7 例：Web 整体视觉、Web 用户流程、科研汇报 PPT、Coding Prompt、Dashboard、科研机制图、普通数组越界修复不触发。
- 扩展路由：Landing Page、Web App/后台、高端 PPT、配色、字体、AGENTS/CLAUDE/Cursor Rules、信息层级/用户体验、图标与插画、报告模板。
- 扩展排除：明确禁止联网、完整参考图严格局部修改、纯算法、翻译、Dashboard 数据加载 Bug。
- 数量契约：2–5 网站、3–8 已检查案例、2–4 核心参考、3–7 规律分别校验；“检查 5 个案例、保留 2 个核心”合法通过。
- 证据契约：有效具体 HTTP(S) URL 或离线路径、事实/观察/推断、相关性、采用、拒绝、项目转译、许可、落实位置与限制。

## 真实前向测试

### 主代理：数据科学课程答辩 PPT

- 打开并分析 Behance 两个具体项目、SlideShare 五页演示、From Data to Viz 具体图型页面。
- 形成结构化和 Markdown Reference Brief；明确 Deck.gallery 无具体可核查结果，因此未伪装为正式来源。
- Gate：`PASS（仅 Reference Brief 阶段）`；PPT 本体不在该测试授权范围。

### 全新代理：GitHub 开源项目健康度 Dashboard

- 全新上下文独立运行，未读取主代理前向测试。
- 打开 4 个网站、7 个具体页面/案例，保留 GitHub、CHAOSS、OSS Compass、From Data to Viz 四组核心参考，提炼 6 条规律。
- 逐项给出事实、观察、推断、采用、拒绝、转译、许可、七类数据状态和下游验收。
- Gate：`PASS（仅 Reference Brief 阶段）`；Dashboard 实现明确为 `N/A`。

## TDD 与修复记录

测试先暴露并随后修复：脚本未存在、七个工作流未接入、Landing/后台/高端 PPT/配色/字体路由合并、禁止联网误触发、Dashboard Bug 误触发、报告模板与视觉资产漏路由、离线空壳误报、伪 URL 可通过、案例数与核心参考数混用、README 描述和分类为空。最终稳定态全部回归通过。

## 结论

`PASS`：所有计划必选项已实现并具备自动化或真实调用证据。状态严格限定在参考路由与 Reference Brief 阶段；本报告不声称任何下游网站、PPT、Dashboard 或科研图已完成构建。
