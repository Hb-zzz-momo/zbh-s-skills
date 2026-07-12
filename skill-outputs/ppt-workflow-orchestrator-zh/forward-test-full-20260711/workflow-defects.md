# Fresh-context 前向测试发现的工作流缺陷

| ID | 缺陷 | 复现/证据 | 影响 | 本轮状态 |
|---|---|---|---|---|
| WF-001 | `validate_contract.py` 文档要求 `sources.md`，旧实现却按 JSON 解析 | `--sources sources.md` 曾触发 `JSONDecodeError` | 正式 Evidence 契约无法原生校验 | 上层在本轮修复并新增 Markdown 回归；最终命令 PASS |
| WF-002 | `check-bounds.ts` 旧规则把合法水平/垂直线的零厚度判为越界 | 原 slice-v1 对 footer-rule/arrow/axis/tick 报 18 个 ERROR | 所有含线条的精细页面被误阻断 | 上层在本轮修复；97/167 元素复验均 PASS |
| WF-003 | 状态机 `full-build` Gate 硬编码未在总控文档声明的 `slice/presentation-slice.pptx`、`slice/montage.png`、`slice/manual-review.json` | 使用契约化 `vertical-slice/` 名称时 Gate 报 missing | 合法产物因命名差异被阻断 | 本轮在输出目录创建同版本别名；建议文档化或允许参数化 |
| WF-004 | 旧 `check_contrast.py` 未解析 slide background、下层矩形与 alpha | 深绿面板白字被按白底误报 | 深色页几乎必然误阻断 | 上层在本轮修复真实背景与 alpha；最终 125 runs PASS |
| WF-005 | `check_geometry.py` 将所有文本框重叠视为错误，无法区分“文字覆盖背景形状”与“文字框互相遮挡” | 初版校样章的边框/文字双对象触发 100% overlap | 合法复合组件会误报 | 本轮通过单对象组件规避；建议后续引入对象角色或容器语义 |

