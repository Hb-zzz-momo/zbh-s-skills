---
name: agent-wait-monitor-zh
description: "Agent 后台监控协议技能：用于长时间任务的后台启动、wait 轮询、进度文件监控、日志监控、卡死判定、自动续跑、失败重试、最终收口和无人值守实验托管。Use when: 后台监控、agent wait、长任务、无人值守、watchdog、自动续跑、卡死恢复、进度轮询、MATLAB长任务、Python长任务、PowerShell后台任务、manifest、checkpoint、结果文件监控。"
---

# Agent Wait Monitor Zh

## 目标

把长任务从“开着终端盯输出”改成可恢复的后台协议：启动后通过 `process + log + result files + manifest` 四类信号判断是否健康，并在卡死或失败时按规则续跑。

## 核心原则

- 进度以结果文件和 manifest 为准，不以终端是否有输出为准。
- 每个 case 完成后立刻落 checkpoint。
- 卡死判定必须同时看进程存在、日志更新时间、结果文件增长和 running 状态持续时长。
- 自动重试必须有上限，超过后进入 hard failed，不要无限重启。
- 监控协议只负责托管，不修改实验口径。

## 标准状态

- `pending`：等待运行。
- `running`：当前正在运行。
- `completed`：结果文件存在且可读。
- `failed_retryable`：失败但可重试。
- `hard_failed`：超过重试上限或确定不可恢复。
- `stalled`：进程存在但结果/日志长期无变化。

## 标准工作流

1. 建 manifest：列出所有预期 case、目标结果文件、状态、重试次数、开始/结束时间、错误信息。
2. 启动 worker：用后台进程、计划任务或 chunk runner 执行少量 case。
3. wait 轮询：固定间隔读取 manifest、日志、结果目录、进程状态。
4. 健康判断：如果 completed 增长或日志更新，继续等待。
5. 卡死处理：如果 running 超过阈值且无结果/日志增长，停止 worker，把 case 回退为 retryable。
6. 续跑：优先 pending，再 failed_retryable；每次完成后写 checkpoint。
7. 收口：pending=0、retryable=0、running=0 后自动汇总；如有 hard_failed，生成失败清单。

## 默认阈值

- 短任务 smoke：`waitInterval = 30s`，`stallMinutes = 10`。
- 中等任务：`waitInterval = 60s`，`stallMinutes = 30`。
- 高维/昂贵任务：`waitInterval = 300s`，`stallMinutes = 120`。
- 单 case 最大重试：`maxRetries = 3`。

实际使用时按任务平均耗时调整，不能把合法慢任务误杀。

## 输出要求

每次建立监控协议时，输出：

- 任务范围和总 case 数。
- 启动命令。
- manifest/checkpoint 路径。
- 日志路径。
- 结果目录。
- 卡死判定阈值。
- 自动恢复策略。
- 最终完成条件。
- 手动查看进度命令。

## 风险边界

- 不要在未确认目标路径时递归删除文件。
- 不要把所有失败都自动重试到死。
- 不要用进程存在作为“正在正常跑”的唯一证据。
- 不要在实验口径未冻结时启动整夜任务。
- 如果用户明确要求不代跑，只生成监控协议和命令，不启动任务。

## 资源

- 协议细则：`references/background-monitor-protocol.md`
- PowerShell watcher 模板：`assets/powershell-watchdog-template.ps1`
- manifest 字段模板：`assets/manifest-schema-template.md`
