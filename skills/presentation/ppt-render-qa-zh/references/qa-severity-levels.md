# QA 严重度

| 级别 | 定义 | 动作 |
|---|---|---|
| BLOCKER | 文件无法打开/渲染、关键页缺失、数据错误 | 停止交付，必须修复 |
| ERROR | 越界、裁切、遮挡、不可读图表、占位文本 | 必须修复并复验 |
| WARNING | 低分辨率、轻微密度/节奏/字体替代 | 修复或说明接受理由 |
| INFO | 可选优化 | 记录，不阻断 |

每条问题记录：`issue_id`, `slide_id`, `severity`, `evidence`, `source_file`, `fix`, `retest_result`。
