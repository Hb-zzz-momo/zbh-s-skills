---
name: decisive-result-audit-zh
description: '决定性结果审计技能：用于审计 formal/gate、冻结版本、论文主表、算法是否胜过基线、是否停止迭代、结果能否支撑论文 claim 等高风险结论；重点检查 raw 结果、collector、metric 实现、summary/gate 表、配置一致性、指标方向和抽样重算是否闭环。Use when: 决定性结果审计, formal审计, gate审计, freeze冻结, 论文主表, 指标审计, raw结果核查, 只有summary没有raw, metric实现未读, 指标输入来源不明, IGD参考前沿, HV参考点, run seed maxFE N metName不一致, collector混用driver, stale历史结果, 抽样重算不一致。'
---

# 决定性结果审计

## 目标

在任何会影响“冻结、论文主表、停止迭代、算法胜负、claim 升级”的结果结论前，先审计代码-指标-结果链路。

本技能不负责判断机制是否堆叠，机制审计继续用 `research-iteration-audit-zh`。本技能只回答：这批结果能不能被相信，指标有没有按正确口径算，比较是否公平。

## 触发等级

必须触发：

- 用户问“结果如何、能不能写论文、是否超过、是否冻结、是否停止、formal/gate 是否通过”。
- 需要解释本项目某次结果中的 `HV / IGD / runtime / min error / rank / win table` 好坏。
- 准备把某个 CSV、summary、gate、rank 表作为阶段性决策依据。
- 发现指标口径、参考前沿、种子、driver、collector、结果目录可能不一致。

不必触发：

- 只问通用概念，例如“IGD 是什么含义”。但一旦涉及“本项目某次结果的 IGD 好坏、是否超过、是否能写入论文”，必须读 metric 实现和输入来源。

## 审计流程

1. **判定结论风险**：标出本结论是否影响论文主表、freeze、gate、停止迭代或算法选择。
2. **列证据链**：写清 raw 文件、collector、metric 函数、aggregate 表、gate 表、报告文件的路径。
3. **读 metric 实现**：正式结果审计必须读取实际 metric 函数和输入来源，不允许只按指标名解释。
4. **查配置一致性**：核对 problem、dataset、algorithm、N、maxFE、run/seed、save、metName、driver、结果根目录。
5. **独立重算样本**：从 raw 结果抽样重算关键指标，至少覆盖 3 个正常样本和 1 个可疑样本；没有 raw 时直接 BLOCK。
6. **查负控和方向性**：确认指标越大越好/越小越好、坏解不会被奖励、排序方向没有反。
7. **给审计结论**：只能输出 `PASS / CAUTION / BLOCK`，并明确哪些 claim 允许、哪些 claim 禁止。

## BLOCK 硬条件

命中任一项直接 `BLOCK`，不得写“看起来差不多”或继续放行：

- 找不到 raw 结果文件。
- 只存在 summary，没有原始 run 记录。
- metric 实现未读，却要解释本项目某次结果的指标好坏或论文结论。
- 指标输入来源不明，例如不知道是 `Population`、`Population.best`、archive 还是最终保存结果。
- IGD 参考前沿未知、fallback、默认点、或没有说明 PF/reference set 来源。
- HV reference point 不明、方向不明、或未确认最小化/最大化口径。
- run、seed、maxFE、N、metName、problem、dataset 配置不一致但被直接比较。
- collector 混用了不同 driver、不同时间批次、不同结果根目录，却没有显式标注和公平性说明。
- 排序方向无法确认，例如 IGD/HV/rank 的升降方向没有核实。
- 抽样重算结果与 summary 不一致，且无法解释差异来源。
- 结果文件缺失、重复、stale，或文件名与数据集/算法/run 不匹配。
- 使用历史结果作正式 gate，却没有证明同配置、同 run 列表和同指标口径。

## CAUTION 条件

以下情况不能直接 BLOCK，但必须降级 claim：

- 历史结果配置一致但不是同一 driver；只能做诊断或补充表，不能写成严格同轮公平对照。
- 只抽样重算了少量样本；允许临时判断，但最终论文表前必须扩大抽样或全量重算。
- 指标本身可用，但任务层指标出现矛盾，例如 HV 高但 min error 或 subset ratio 明显异常。
- 结果来自多个 step 的合并；必须说明合并规则和缺失处理。

## PASS 条件

全部满足才可 `PASS`：

- raw 文件、collector、metric 实现、summary、gate 链路完整。
- 指标参考集、方向、输入对象明确。
- 同配置公平性成立，或历史引用边界已写清。
- 抽样重算与 summary 一致。
- 结论只覆盖证据能支撑的范围。

## 输出格式

正式使用时，在当前工作区输出 Markdown 审计报告。建议保存到 `skill-outputs/decisive-result-audit-zh/`。

报告必须包含：

- 审计对象和决策风险。
- 证据链路径表。
- 配置一致性表。
- metric 契约表。
- 样本重算表。
- `PASS / CAUTION / BLOCK` 结论。
- 允许写入论文的 claim 与禁止 claim。

报告模板见 `assets/audit-report-template.md`。指标红旗清单见 `references/metric-red-flags.md`。
