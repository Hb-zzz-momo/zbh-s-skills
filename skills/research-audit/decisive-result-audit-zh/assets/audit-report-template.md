# 决定性结果审计报告 - <对象>

**审计时间**：<YYYY-MM-DD HH:MM>  
**审计对象**：<step / result / table / claim>  
**决策风险**：<论文主表 / formal gate / 冻结版本 / 停止迭代 / 诊断性结论>  
**最终判定**：<PASS / CAUTION / BLOCK>

## 1. 一句话结论

<这批结果能否用于当前决策；不能时说明最短根因。>

## 2. 证据链

| 环节 | 文件/函数 | 状态 | 备注 |
|---|---|---|---|
| 原始结果 raw | <path> | <OK/MISSING> | <说明> |
| 指标实现 metric | <path/function> | <READ/UNREAD> | <说明> |
| collector | <path> | <OK/MISSING> | <说明> |
| 汇总表 aggregate | <path> | <OK/MISSING> | <说明> |
| gate/报告 | <path> | <OK/MISSING> | <说明> |

## 3. 配置一致性

| 字段 | 当前结果 | 对照结果 | 判定 |
|---|---|---|---|
| problem | <value> | <value> | <OK/DIFF> |
| dataset | <value> | <value> | <OK/DIFF> |
| N | <value> | <value> | <OK/DIFF> |
| maxFE | <value> | <value> | <OK/DIFF> |
| run/seed | <value> | <value> | <OK/DIFF> |
| metName | <value> | <value> | <OK/DIFF> |
| driver/结果根目录 | <value> | <value> | <OK/DIFF> |

## 4. 指标契约

| 指标 | 方向 | 输入来源 | reference/PF | 已读实现 | 判定 |
|---|---|---|---|---|---|
| HV | 越大越好 | <source> | <ref> | <yes/no> | <OK/BLOCK> |
| IGD | 越小越好 | <source> | <PF/ref> | <yes/no> | <OK/BLOCK> |

## 5. 抽样重算

| 样本 | summary 值 | 重算值 | 差异 | 判定 |
|---|---:|---:|---:|---|
| <dataset-alg-run-metric> | <x> | <y> | <d> | <OK/DIFF> |

## 6. BLOCK 检查

- [ ] 找不到 raw 结果文件。
- [ ] 只存在 summary，没有原始 run 记录。
- [ ] metric 实现未读却解释本项目结果。
- [ ] 指标输入来源不明。
- [ ] IGD 参考前沿未知或 fallback。
- [ ] HV reference point 不明。
- [ ] 配置不一致但直接比较。
- [ ] collector 混用不同 driver 或批次。
- [ ] 排序方向无法确认。
- [ ] 重算样本与 summary 不一致。

## 7. 允许和禁止的 claim

允许：

- <claim>

禁止：

- <claim>

## 8. 下一步

<修复指标、补 raw、重跑同配置、重算 PF*、降级 claim 等。>
