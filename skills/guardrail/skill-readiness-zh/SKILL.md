---
name: skill-readiness-zh
description: Skill 调用前的依赖就绪检查与全库状态盘点，分别核验工具、版本、资料、账号服务和活动 MCP；缺失、未知、过期均阻断执行。用于调用前检查、工具资料补齐、Skill 状态、环境是否安装齐全；不把技能可读当作功能可用。
metadata:
  version: "1.0.1"
---

# Skill 状态与执行前检查

本技能是用户要求的全局执行门禁，覆盖直接点名、主技能、辅助技能、跨技能跳转，以及 `.agents`、`.codex`（含 `.system`）和插件来源。安装说明、下载缓存、MCP 注册、工具出现在列表、实际功能验证是不同证据。

## 引导边界

允许先读取 Skill、检查依赖、生成清单和修复计划；这些是准备动作，不等于已执行领域工作流。门禁脚本只依赖 Python 3.11+ 标准库，先用 `python --version` 确认即可启动检查，避免门禁递归调用自身。缺 Python 时停止脚本，报告缺项；可只读核查，不能伪造 READY。

## 调用前

1. 定位本次实际加载的 Skill **绝对路径**，读取完整正文与其工具/资料声明。已有同名技能按来源和版本分别登记；不要拿另一个来源的状态替代。首次或升级后用 `draft` 建清单，人工/agent 逐项审阅依赖完整性；抽取草案默认未审阅。
2. 用下方 `check` 对这个实际路径执行实时检查。依赖不齐、版本不符、引用资料缺失、无法解析、未知或过期时不得执行相应工作流，也不得声称已经调用成功。只读准备可继续。
3. 资料包括本地 references/assets/scripts、外部必需文档、模板、模型和数据；外链不能用“能打开”代替“已取得匹配版本”。必需外链提供本地文件与 SHA-256，纯引用需逐项写明理由，不能批量把运行资料降为参考。云服务检查连接、权限及实际只读探测，不虚构可下载的云工具。
4. 默认检查 **full**：所有已声明工具和资料都登记；平台不支持也不能伪装安装完成。若用户明确选择某个任务范围，可按已审阅 profile 检查并记录 `--scope-reason`；保留未选依赖与全技能未齐备状态。未经范围选择不能自行用最小分支替代用户的“所有”。
5. 每次执行前重查；Skill/资料/依赖清单/解释器/工具版本/环境/账号/会话变化均使旧结论失效。状态表只是快照，不是永久通行证。MCP 使用当前会话工具清单和成功只读调用证据；会话证据须匹配当前 session_id 且不超过 5 分钟。

```powershell
# 脚本路径相对于本技能目录；本地状态不得提交 Git。
python scripts/skill_readiness.py inventory --output "$env:USERPROFILE/.agents/.local/skill-readiness/STATUS.json" --markdown "$env:USERPROFILE/.agents/.local/skill-readiness/STATUS.md"
python scripts/skill_readiness.py draft --skill "<实际技能绝对路径>" --output "<外置清单绝对路径>"
python scripts/skill_readiness.py check --skill "<实际技能绝对路径>" --manifest "<已审阅清单绝对路径>"
```

check 仅 READY 返回 0；其他状态返回非零。inventory 返回 0 仅表示发现过程成功，不代表任何技能已经就绪。没有清单、清单未审阅或资源指纹变化都不能通过。清单协议及受支持探测见 [references/contract.md](references/contract.md)。

## 状态与展示

| 状态 | 含义 | 能否执行 |
|---|---|---|
| READY | 此路径、版本、范围的全部检查有当前证据 | 仅允许声明范围 |
| UNKNOWN | 未审阅、未分类或缺功能证据 | 否 |
| BLOCKED | 工具/资料缺失、版本不符或平台不支持 | 否 |
| STALE | 材料变化或会话证据过期/不匹配 | 否 |
| ERROR | 检查异常、无效输出或超时 | 否 |

单项可另外显示 MISSING、INCOMPATIBLE、NOT_SELECTED、UNSUPPORTED_HOST、REFERENCE_ONLY。未选和平台限制不等于下载完成。反馈至少包含实际 Skill 路径/版本、检查时间、范围、状态、缺项及证据；不为普通任务反复输出长清单。

## 清单维护与修复

- 原生组件故障时，按 [开源替代规则](../skill-router-zh/SKILL.md#原生组件故障的开源替代) 主动查找插件/MCP；沿用当前授权和工具约束，对所选替代路径重新核查依赖、连接与真实目标。外置客户端可用和当前聊天已连接分别登记，不沿用原组件或其他会话的 READY。
- 软件/依赖和运行状态留本机 `.agents/.local/skill-readiness/`；可迁移的检查程序、协议、经核实依赖定义与回归测试纳入技能仓库。
- `.system` 和供应商插件缓存不批量改写，使用外置清单；全局规则和直接入口同样约束它们。清单文件名由实际技能绝对路径 SHA-256 决定，防同名误用。
- 新技能/更新后重盘点。读取其全包并修订清单，不能只重新计算摘要后把旧审阅标志照抄。
- 缺项先找已安装路径和已有运行时；给出来源、兼容版本、体积/授权/平台限制与验证方式，再在已授权范围修复。不得为检查自动安装无关引擎、购买许可证、改授权或泄露配置。
- REA 按 [REA 清单说明](references/rea-readiness.md) 先分清缓存、Node、CLI、注册、会话和引擎；doctor 的健康结果也不代替当前会话连接与目标分析证据。

## 验证与能力边界

运行 `python scripts/test_skill_readiness.py`。正常路径、失败路径、所有来源发现、直接入口的前向评价都应保留证据。全局文字规则与 check 非零退出共同约束 agent；本技能**没有修改 Codex 宿主实现，也不能声称在宿主层拦截了每一个工具调用**。

本次验收矩阵、原始问题、三轮修订和真实结果见 [validation-and-reflection.md](references/validation-and-reflection.md)。测试通过仅证明门禁已测行为，不能证明全库工具和资料已经全部安装。
