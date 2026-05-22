# Manifest 字段模板

| 字段 | 说明 |
|---|---|
| CaseId | 唯一编号 |
| DataNo | 数据集编号或任务编号 |
| DataName | 数据集或任务名称 |
| Algorithm | 算法或执行器 |
| Run | run 编号 |
| ExpectedFile | 目标结果文件 |
| Status | pending/running/completed/failed_retryable/hard_failed |
| RetryCount | 已重试次数 |
| LastError | 最近错误 |
| LastStartTime | 最近启动时间 |
| LastFinishTime | 最近结束时间 |
| WorkerPid | 执行进程 PID |
| LastHeartbeat | 最近心跳或日志更新时间 |

## 状态迁移

```text
pending -> running -> completed
running -> failed_retryable -> pending
failed_retryable -> running
failed_retryable -> hard_failed
running(stalled) -> failed_retryable
```
