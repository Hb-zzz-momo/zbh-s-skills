# REA 依赖检查

本机曾验证：Skill v49，REA npm 缓存 6.8.0，Node 24.19.0；包要求 `^22.23.4 || ^24.22.1 || >=26.12.1`。Codex 无 REA 注册、会话无 REA 工具；各引擎未配置。此为 2026-11-02 观察，不能永久沿用。

检查顺序：

1. 查本地实际 npm 包和公开 launcher，读取 package.json 的 engines，不能把缓存命中当可执行通过。不为检查再次下载 latest。
2. `node --version` 与**该包**要求比较；CLI 自身版本也记录。
3. 使用已安装的公开 launcher 执行 `doctor --client codex --json`，保存完整输出；分清 runtime、registration、provider 与 skill copy 的诊断。
4. 从当前真实会话找 REA 工具并实际执行只读健康查询；doctor 无法证明当前 agent 已连接。命令行可用也不能冒充 MCP 可用。
5. 引擎分别记录：Ghidra+Java、Hopper、IDA、Kuna、Android JADX 等；固件、网络、WASM、信号等分支还有独立依赖。按完整 Skill/引用文档审阅，未全部审清则全技能 UNKNOWN，不能只列几个常见引擎后设 complete=true。
6. 完整状态与明确范围的状态分开。Windows 未安装 macOS 专用组件、未选择替代引擎、缺账号/运行环境都有单项状态；不得称“所有工具齐全”。

用户在本轮明确选择全部登记、按本机任务严格检查，并授权补齐 Windows REA 环境。已准备便携 Node 24.22.1、Temurin JDK 21.0.13+9、Ghidra 12.1.4；官方校验及 Ghidra 原始样本分析见独立工具链记录。REA CLI/MCP 与实际 PE 反编译另验收，不能把工具下载完成等同连接完成。未选择的其他平台和替代引擎继续如实保留状态。

## 2026-11-02 修复后的已核范围

- 官方 REA Skill 从 v49 同步到 v59，固定 main 提交 2ac6d3efe2d1a37176da3bc811156b37abe51619，保留本地门禁补丁。npm 最新正式版仍是 6.8.0，包期望 Skill49；不能将 main 文档的新工具视为已发布能力。
- Windows profile 仅包含本机原生 PE 静态验证：Node24.22.1、JDK21、Ghidra12.1.4、REA6.8.0、匹配的 Windows native addon、bridge、实际 schema、离线 Windows P0 说明和自有连接。
- profile 的运行时检查采用固定只读 `rea --version`、指定 provider 的 doctor、官方 `rea mcp doctor`；后者完成初始化、229 个工具目录与实际 binary_session 请求，验证自有新连接，不等于当前聊天已加载工具。
- 自建、手工编码的 PE64 DLL（1536 字节）经实际 open_binary → analyze_function → export_evidence_bundle → close_binary 完成静态分析；伪代码恢复减法、最低值和暴击翻倍；8 个本地算术用例也符合参考。此为工具链自检，不是用户游戏的逆向成果。
- 普通用户打包验证全套尚未执行；本次在当前管理员 token 下验证。Windows P0 平台/NTFS/不可变良性目标等限制保留。6.8.0 未广告 reset_investigation，未调用该工具，证据先导出再关闭自有连接。
- 本机门禁结果保存在 `.agents/.local/skill-readiness/rea-windows-native-static.json`，profile 可 READY，full_skill_ready 必须 false；全技能其他能力仍待审阅/补齐。当前 Codex 聊天工具目录无 REA，需客户端重新加载后重新查活动会话，不用自有连接证据替代。

### doctor 的一个易误读点

doctor 默认可能检查 `.agents/skills/reverse-engineer-anything` 共享副本，而实际可见技能位于 `.codex/skills/reverse-engineer-anything`。报告共享副本缺失不能抹掉实际副本已存在这一事实；同样，实际副本存在不能抵消 Node/引擎/连接缺失。
