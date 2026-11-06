# 就绪清单与探测协议

## 位置与身份

源文件 `SKILL.md` 与完整包材料只读检查；不写供应商缓存。维护者依赖声明可放技能目录 `readiness.json`。Windows 的本机外置清单默认放 `D:/CodexData/skill-readiness/manifests/<实际技能绝对路径的sha256>.json`，其他系统沿用 `~/.agents/.local/skill-readiness/manifests/`；`check --manifest` 可指定明确文件。默认读取顺序是包内声明、新状态目录、旧用户目录清单；旧 C 盘内容只读兼容，不自动迁移或删除。Windows 的 JSON/Markdown 输出在创建父目录前解析路径，必须实际位于 D 盘（D→C 联接、其他卷和 UNC 均拒绝），盘符不可用直接报错，不回退 C；JSON 暂存文件在已解析的目标目录独占随机创建，不沿用现有 `.pending` 文件或链接。此限制只覆盖本脚本输出，不代表系统级写保护；启动者仍须把 Python 临时文件等子进程写入路径放 D 盘。

同一 Skill 被多个项目或任务使用时，任务专属目标、会话证据和依赖选择使用各自验证目录的独立 manifest，并显式传 `--manifest`；不要覆盖中央默认清单中其他任务的已审范围。中央表是全库快照，任务验收记录另保留范围、版本与时间，不能用某个任务 READY 替代全技能状态。

默认扫描 `~/.agents/skills`、`~/.codex/skills`（包括隐藏 `.system`）、`~/.codex/plugins/cache` 的物理包。插件缓存中的旧版本也单列，不声称每个都在活动目录；实际调用检查实际加载路径。自定义 `--root 来源=路径` 必须列全本次范围，缺根/读取失败记发现错误，不能把扫描子集说成全库。

资源指纹覆盖包中实际文件及 Markdown 相对链接的递归闭包（含包外文档），支持行内链接、引用式定义和 HTML src/href；循环去重。符号链接目录、不支持解析或目录型引用保持未知，达到闭包上限也不通过。绝对路径参与指纹，换机需重新审阅。不会为了通过而删除坏链接。正文中的示意路径/生成后路径如被识别为缺失，须修正文档表达或提供带理由的人工核实，不能改成全局忽略。

## 草案与审阅

`draft` 生成以下形状，默认不允许执行：

```json
{
  "schema_version": 1,
  "skill_name": "actual-name",
  "bundle_sha256": "由 draft 计算，不手写",
  "review": {"complete": false, "reviewer": "", "note": ""},
  "requirements": [],
  "remote_materials": {},
  "profiles": {}
}
```

审阅者读取完整正文、相关脚本、资源和环境说明，核对所有工具、运行时、包、账号、服务、模型、数据及外部资料后补清单。`review.complete=true` 是明确的完整性审阅声明，不是自动抽取的结论；未读完或无法确认则保留 false。无工具的纯指令技能也须确认资源完整，不把“没抽到”当“无依赖”。

完整审阅后运行 `python scripts/skill_readiness.py definition-digest --manifest <清单路径>`，将输出记录为 `review.definition_sha256`。摘要覆盖除 review/profile_reviews 审阅记录外的全部定义；更改 requirements、remote_materials、profiles 或身份后沿用旧摘要会返回 STALE，须重新审阅。这防误沿用，不能证明审阅者没有主动伪造审阅。显式指定的清单路径不存在会报错，不静默改用其他清单；返回值记录实际 manifest_path。

依赖条目必须唯一 `id`。支持：

- `executable`：`command` 与 `version_args`；仅允许 `--version`、`-version`、`-V`、`/version`，无 shell、超时 10 秒；仅找到文件保持 UNKNOWN。支持 `minimum`、`exact_version` 或 `accepted_versions`（major/minimum/maximum_exclusive）。不执行任意命令字符串。
- `rea_package`：检查本地 npm 缓存/全局位置的包元数据与公开 launcher，只证明包文件存在，不代表运行环境、CLI 或 MCP 健康。
- `rea_probe`：显式 `node`、公开 `launcher`、`mode=cli/ghidra/mcp`；只运行固定版本命令、指定 Ghidra doctor 或官方 `rea mcp doctor`，最多 60 秒。环境仅接受 JAVA_HOME/GHIDRA_INSTALL_DIR；MCP 模式要求实际 binary_session 请求成功，**它验证新建的自有连接，不能冒充当前聊天连接**。其他模式和任意命令不执行。
- `file`：`path`，可加 `sha256`；外部必需资料必须有 SHA-256。目录/模型集合需显式逐文件清单或另写只读验证适配器。
- `python_distribution`：`distribution` 与版本条件，通过当前解释器的包元数据检查；若技能还需实际导入/业务操作，应另补真实探测证据，不能只凭包元数据宣称完整可用。
- `mcp_registration`：Codex TOML 的 `path`、`server`；仅检查存在且启用，不输出配置秘密，不代表连接或账号权限。
- `session_tool`：`name_pattern`，核对本次工具列表。`session_health` 还要求成功只读调用的 operation 与 evidence_id。二者分开登记。模板填充或人工伪造 evidence_id 不成立。
- 其他 `kind` 保持 UNKNOWN；确需网络、授权账号或特定引擎时补只读适配器与测试，不用静态字符串覆盖。

`profiles` 的每个值为对象，描述明确任务并可包含该范围专用 remote_materials；依赖条目可带 profiles 列表。完整技能的审阅放 review；每个范围独立放 profile_reviews[范围名]（complete/reviewer/note/definition_sha256）。完整技能未审完不妨碍已独立审完且获用户选择的具体任务；全技能审阅也不自动批准新增范围。

默认 full 不跳过任何条目。选择其他 profile 必须记录用户明确选择的理由；full_skill_ready 永远为 false。共享依赖不带 profiles，任何范围都检查。profile 不得绕过资料未知或实际执行必需项。其专用 remote_materials 可逐项列 classification=not_selected 与具体分支理由，记录为 NOT_SELECTED，不代表已下载；全量仍按原定义检查。inventory 的范围检查仅作只读盘点，无任务执行许可。全量和范围状态均会展示。

## 远程资料

正文外链默认 UNKNOWN。必需材料声明 `classification=material`、本地 `path` 与 `sha256`；仅作出处/进一步阅读的链接声明 `classification=citation` 并给具体 `reason`。禁止通过批量 citation 处理把工具文档、模板下载或执行资源隐藏。上游版本变化要重新取得匹配材料并复核。

## 当前会话证据

调用者从真实工具目录生成 `--session-tools` 快照，并用 `--session-id` 指定本次会话身份：

```json
{
  "session_id": "当前真实会话标识",
  "observed_at": "当前UTC时间",
  "tools": ["实际工具全名"],
  "health": {
    "实际工具全名": {"ok": true, "operation": "真实只读操作", "evidence_id": "实际返回或保留证据的标识"}
  }
}
```

5 分钟以上、未来时间异常、其他会话或没有真实成功调用均不能当健康。快照是 agent 提供的证据文件，不是独立认证机制；禁止声称本脚本能够证明人没有伪造输入。连接变化立即重取，不等过期。

## 退出语义

check：READY=0；UNKNOWN/BLOCKED/STALE=2；输入或检查异常=3。inventory：发现完整=0；发现缺根等错误=2；不以退出 0 代表技能就绪。draft：生成草案=0，不是允许执行。输出与状态含具体范围、时间、材料指纹、单项证据及缺口。

## 外部依据

- [Agent Skills 规范](https://agentskills.io/specification)定义包资源和元数据，没有保证依赖自动安装；本门禁是用户级扩展。
- [MCP 工具规范](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)区分工具列表和实际调用；注册、可见与调用健康按不同证据处理。
- REA 本地 v49 说明明确技能不安装 MCP/引擎，本门禁保留这一边界并加上执行前状态。
