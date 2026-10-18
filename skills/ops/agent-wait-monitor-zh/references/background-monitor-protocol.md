# 后台监控协议细则

## 四类健康信号

| 信号 | 说明 | 不能单独依赖的原因 |
|---|---|---|
| 进程 | MATLAB/Python/PowerShell 是否存在 | 进程可能卡死 |
| 日志 | stdout/stderr/log 是否更新 | 有些任务长时间无输出 |
| 结果文件 | 目标 `.mat/.csv/.json` 是否新增 | 只在 case 完成时变化 |
| manifest | pending/running/completed/failed 状态 | 需要和文件互相校验 |

## 卡死判定

建议同时满足以下条件再判定 stalled：

- running 状态持续超过 `stallMinutes`
- 日志未更新超过 `stallMinutes`
- 结果文件数量未增长
- 当前 case 没有进入 completed 或 failed

## 恢复策略

1. 停止当前 worker。
2. 把残留 running 回退为 pending 或 failed_retryable。
3. RetryCount + 1。
4. RetryCount < maxRetries 时继续跑。
5. RetryCount >= maxRetries 时标记 hard_failed。
6. 重新启动 worker 继续 pending 队列。

## 完成条件

严格完成：

- completed == expected
- pending == 0
- running == 0
- failed_retryable == 0
- hard_failed == 0

宽松完成：

- pending == 0
- running == 0
- failed_retryable == 0
- hard_failed > 0
- 已输出 hard_failed 清单和失败原因

## 进度报告格式

```text
Total: 7200
Completed: 6150
Pending: 930
Running: 1
Retryable: 118
HardFailed: 1
LastResultTime: 2026-04-24 22:10:03
Conclusion: continue / stalled / completed / hard_failed_needs_decision
```
