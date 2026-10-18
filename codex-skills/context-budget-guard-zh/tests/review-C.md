# 独立评审 C：前向场景验证原始意见

结论：**PASS（仅本轮场景及规则一致性范围）**。未发现导致误报无变化、弱化验收、覆盖原件或越界记忆写入的必改缺陷。不是整体发布验收，也不代表性能无损承诺。保留下述操作边界与未验证项。

## 身份、版本与独立性

- 真实代理身份：`/root/workflow_review`，由父代理 `/root` 分派为独立评审 C；本记录由此代理独立形成。未读取其他评审记录，未递归委派，未修改技能、冻结文件或发布。
- 未获得可核验的运行模型名称，不猜填型号。结论依据本记录中的文件原文与真实命令结果。
- 输入：`frozen-r1`；标准：同级 `acceptance.md`；哈希清单：`frozen-r1-hashes.json`。初读及收口复算 7/7 一致，详见末尾清单；主技能 SHA256：`279C4C4BD8ED8D9549E7B9708D7430356BCFA6A8A591EA0365B46A07B71D9529`。
- 已读取持续授权评价技能 `C:/Users/zbh/.agents/skills/guardrail/multi-agent-evaluation-zh/SKILL.md`。仅写本记录和系统临时目录。
- 评审方法：规则前向推演 + 自建临时项目真实 CLI。算术输入 3、5 与结果 8 来自真实执行；项目身份、课程要求和平台待办是明确标注的模拟材料，不冒充真实学生实验、截图或教师平台事实。

## 先定预期行为

1. 用户新要求重跑优先于旧状态；截图待复核、运行进程、教师平台外部状态必须保留为待办/外部依赖并读取实际来源。即使静态文件相同，也不能结束原任务。
2. 长背景可用抽取式导航压缩；数字、代码/命令、引文/来源、模板、验收条件、身份/路径逐字保留。三位评审各拿完整目标、验收约束、冻结范围和来源指针，初评不共享作者预期或其他评审意见，原件可追加读取。
3. 单次简单小改直接完成；确有重复观察成本才接入。首次先读规则、现有入口和原证据并实际验证、更新地图，再 record。check 不写基线；变化需先处理，不自动 record；坏基线停用优化并保留现场。

## 场景 1：旧哈希相同，但要求重跑且仍有待核验状态

原文依据：`SKILL.md:14,29-33`；`references/operation.md:10-11,29-33,44-45`。

实际构造：有限清单含规则、代码、测试、真实输出、报告、环境和地图共 8 文件；在 manifest 保留“截图待独立复核”及进程/教师平台依赖。先执行 `calc.py` 和算术断言测试，再登记本地核验时间与地图，record 时明确外部状态尚未核验。record 仅记观察，不宣称验收完成。

真实结果：首次 check=`CHANGED/1`，record=`RECORDED/0`；原文件和 evidence_hash 均未变化时，check=`REVIEW_REQUIRED/1`，`can_skip_repeated_analysis=false`，state 字节 SHA256 不变。另实际重新运行了一次算术任务，输出仍为 `{"left": 3, "right": 5, "sum": 8}`，没有以旧哈希拒绝新运行；未推进或修复观察基线。

前向处置：真实课程任务仍须运行用户授权的实验并核查真实进程/日志；截图应交规定的真实评审或人工来源；平台必须读取平台状态。拿不到平台/截图证据只能保留待核验，不能把算术测试或文件相同写成外部已通过。此轮未访问真实平台、未执行真实课程实验。

结论：PASS。本技能不会按其规则允许该场景“一行无变化”收工。脚本不接收当前自然语言指令，因此新任务判断必须由助手按 SKILL.md:30 完成；任何绕过该判断的外部自动化均不在本轮通过范围。

## 场景 2：长任务交三位独立评审，各自精简材料

原文依据：`SKILL.md:39-44,48`；`assets/maps.md:12-19,25-30,34-37`；`references/operation.md:48-49`。

实际构造：150 行重复历史背景 + 完整保护块；保护块包含实际执行数字 3、5、8，命令 `python -B calc.py`，原始 JSON 引用，本地模板顺序，完整验收条件，模拟身份 `student-demo-20261019`、报告路径与 scope。抽取保护块制作 A/B/C 三个样例材料包，维度分别为代码/数字、模板/引用、身份/边界。每包附相同 fixture-v1 原件入口、9 个原件 SHA256、相关地图和可追加读取说明。

真实校验：三包都包含逐字相同保护块；保护块 UTF-8 SHA256 均为 `ac6116c52d675302ef74a28cc7897a8f7c1879d4f40413fe838bb460f64ac398`。仅压缩背景，没有用助手归纳替换保护块。地图中的真实签名、测试入口、状态/来源和身份字段在模板中齐备；“登记测试入口不等于通过”和“哈希相同与正确分开记录”均明确。

必须说明：A/B/C 是本轮材料样例名，不是新创建的三位真实代理，也没有伪造三人评分。此轮依父任务禁止递归委派，只验证材料准备能遵守规则；实际三位评审的行为、理解一致性和漏项率未测。每位真实评审若独立生成摘要，该摘要仍须保留来源，不能汇总成唯一证据；原始意见与修订复验照常保留。

记忆与压缩边界：3–8 条是软目标，无相关记忆不凑数，超过 8 条关键约束也不得删减；任务收尾只在现有任务记录追加有来源的候选，用户原话与助手归纳分开。没有调用全局记忆接口，没有安装/调用 LLMLingua、Mem0、LangMem、Graphiti，也没有创建后台任务。上述行为限制可由规则直接成立，不能由摘要评分代替原件核验。

结论：PASS（材料规则和保护块样例）；真实三人评审效果未验证。

## 场景 3：小改旁路、重复本地观察与 record 时机

原文依据：`SKILL.md:12,15,19-22,24-35,52`；`references/operation.md:3,7-11,23,29-39`。

单次小改：例如只改一处标题，按规则直接改并做相应验收，不需要代码地图、manifest、哈希或记忆候选；本次没有为了这个例子单独建立缓存。旁路条件是成本判断而非脚本自动识别；目前规则足以允许省掉维护，未强制将普通小改变成长期任务。

重复本地任务：从“含真实外部待办的课程模拟范围”切到独立的“仅本地加法验证范围”，变更 scope/current_status 后得到 `CHANGED/1`，没有把待办当成完成，也没有在原课程 scope 为了得到无变化而清空待办。已有真实本地执行、断言测试和地图读取后再 record，随后纯观察=`UNCHANGED/0`。

故障/变更实测：将报告结果 8 改为 9，保持文件尺寸与 mtime 相同；check 仍返回 `CHANGED/1`，仅定位 `report.md`/report。连续两次 check 均为 CHANGED，state 文件字节不变。复读原始 JSON 确认 8 后恢复报告原文，原基线再次匹配。最后故意把临时 state 改成损坏 JSON，check=`UNKNOWN/2`，原损坏字节保留，未调用 record 掩盖损坏。

性能证据仅限 1227 字节、8 文件样例：CLI 内部 elapsed_ms 约 20.83–75.57 ms；这不含 Python 启动，不是完整用户响应耗时或代表性性能评测。2 秒预算、固定上限及无法中断 OS I/O 的限制已在原文明确，不应承诺百分比节省或性能完全不变。

结论：PASS。旁路与异常降级清楚；真实命令未发现自动推进基线。

## 发现、严重性、改法与复验

| 项目 | 严重性/结论 | 原证据 | 最小改法与复验 |
| --- | --- | --- | --- |
| 必改阻断缺陷 | 未发现 | 上述三个场景和原始 CLI | 不提出强制修改；修订版本仍须按受影响范围重验 |
| `can_skip_repeated_analysis=true` 仅表示静态资格，不能判断新用户指令 | 非阻断操作风险；现有规则已约束 | `scripts/context_snapshot.py:238-244`，`SKILL.md:30`，operation:29 | 可选在 JSON 增加 `requires_current_task_gate=true` 作为机器使用提示，或把布尔字段名改为“静态候选”；非必要变更。若改，复验 UNCHANGED + 新指令仍执行任务 |
| 地图/压缩的端到端节省与漏项率 | 未验证边界，不是已发现退化 | 本轮只验证 8 文件临时项目与三份样例包 | 若未来要宣称收益，选真实长任务测读量、总耗时和验收漏项；本次无需增加平台、依赖或常驻任务 |

本结论不要求为可选改法扩大本轮任务，也不要求安装任何组件。不得据此绕过领域验收。脚本读写边界从源代码可见仅标准库、本地有限清单、check 读文件、record 写缓存 state/临时锁；没有网络/模型/记忆调用。

## 未验证边界

未检验真实 Word/PDF 页面、图片人工判断、课程实验再运行、教师平台/云同步/生产进程的状态；没有执行代表性大项目性能基准；未在此轮覆盖所有权限/重解析点/64 文件/32 MiB/锁竞争等失败矩阵；源码读过但完整自动单元测试交父任务/其他限定评审处理；未独立验证安装目录镜像、Git 提交推送或远端 HEAD。

只通过当前冻结版本的前向规则与列出的 CLI 场景，不把此记录替代上述验收。

## 原始执行证据

临时目录：`C:\Users\zbh\AppData\Local\Temp\context-budget-review-C-1fefdaae4d59453e91e716d7527e3e5a`。保留 `review_harness.py`、`rerun_check.py`、`pack_freeze.py`、project 原件、三份 pack 与 results.json。为了临时目录清理后仍可回查，完整 CLI 原结果嵌入如下。新增重跑测试在故障测试之后执行，因此它不用于证明损坏基线已修复，也没有这种修复。

```json
{
  "temp_root": "C:\\Users\\zbh\\AppData\\Local\\Temp\\context-budget-review-C-1fefdaae4d59453e91e716d7527e3e5a",
  "python": "3.14.0 (tags/v3.14.0:ebf955d, Oct  7 2025, 10:15:03) [MSC v.1944 64 bit (AMD64)]",
  "executed_utc": "2026-10-18T17:51:59.645716+00:00",
  "fixture_notice": "Temporary synthetic project, actual arithmetic code execution, no real lab or teacher-platform claim.",
  "results": [
    {
      "label": "S1 initial no baseline",
      "exit_code": 1,
      "result": {
        "status": "CHANGED",
        "message": "CHANGED",
        "can_skip_repeated_analysis": false,
        "scope_id": "review-C/demo/student-demo-20261019",
        "evidence_hash": "f949c8e5ebbdbcdfc82309a90bdf24fc59d269aeec7547659b2a3ca431c94b5b",
        "current_status": "本地加法已执行验证；外部平台状态未获取",
        "changed_paths": [
          ".context-cache/code-map.md",
          ".context-cache/evidence-index.md",
          "calc.py",
          "environment.txt",
          "raw-result.json",
          "report.md",
          "requirements.md",
          "test_check.py"
        ],
        "changed_fields": [
          "code",
          "code_map",
          "environment",
          "evidence_map",
          "manifest_or_scope",
          "report",
          "requirements",
          "results",
          "test"
        ],
        "observed_bytes": 1227,
        "elapsed_ms": 75.57,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "label": "S1 record after local actual execution and maps; issues retained",
      "exit_code": 0,
      "result": {
        "status": "RECORDED",
        "message": "RECORDED",
        "can_skip_repeated_analysis": false,
        "scope_id": "review-C/demo/student-demo-20261019",
        "evidence_hash": "f949c8e5ebbdbcdfc82309a90bdf24fc59d269aeec7547659b2a3ca431c94b5b",
        "current_status": "本地加法已执行验证；外部平台状态未获取",
        "changed_paths": [
          ".context-cache/code-map.md",
          ".context-cache/evidence-index.md",
          "calc.py",
          "environment.txt",
          "raw-result.json",
          "report.md",
          "requirements.md",
          "test_check.py"
        ],
        "changed_fields": [
          "code",
          "code_map",
          "environment",
          "evidence_map",
          "manifest_or_scope",
          "report",
          "requirements",
          "results",
          "test"
        ],
        "observed_bytes": 1227,
        "elapsed_ms": 39.55,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "label": "S1 unchanged files but screenshot/external states pending",
      "exit_code": 1,
      "result": {
        "status": "REVIEW_REQUIRED",
        "message": "REVIEW_REQUIRED",
        "can_skip_repeated_analysis": false,
        "scope_id": "review-C/demo/student-demo-20261019",
        "evidence_hash": "f949c8e5ebbdbcdfc82309a90bdf24fc59d269aeec7547659b2a3ca431c94b5b",
        "current_status": "本地加法已执行验证；外部平台状态未获取",
        "changed_paths": [],
        "changed_fields": [],
        "observed_bytes": 1227,
        "elapsed_ms": 29.62,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "label": "S1 check preserves state bytes",
      "passed": true
    },
    {
      "label": "S2 pack-A",
      "protection_sha256": "ac6116c52d675302ef74a28cc7897a8f7c1879d4f40413fe838bb460f64ac398",
      "verbatim_protection": true,
      "bytes": 3430,
      "frozen_originals_with_sha256": 9,
      "maps_and_source_paths_present": true
    },
    {
      "label": "S2 pack-B",
      "protection_sha256": "ac6116c52d675302ef74a28cc7897a8f7c1879d4f40413fe838bb460f64ac398",
      "verbatim_protection": true,
      "bytes": 3427,
      "frozen_originals_with_sha256": 9,
      "maps_and_source_paths_present": true
    },
    {
      "label": "S2 pack-C",
      "protection_sha256": "ac6116c52d675302ef74a28cc7897a8f7c1879d4f40413fe838bb460f64ac398",
      "verbatim_protection": true,
      "bytes": 3427,
      "frozen_originals_with_sha256": 9,
      "maps_and_source_paths_present": true
    },
    {
      "label": "S3 scope changed and local-only requirement reassessed",
      "exit_code": 1,
      "result": {
        "status": "CHANGED",
        "message": "CHANGED",
        "can_skip_repeated_analysis": false,
        "scope_id": "review-C/local-addition-only/student-demo-20261019",
        "evidence_hash": "cbc3925a989f8a8f5154e188657bb2ff50c9217b5439f615d4f31cbfd0adf5ed",
        "current_status": "仅验证临时本地加法与输出",
        "changed_paths": [],
        "changed_fields": [
          "manifest_or_scope"
        ],
        "observed_bytes": 1227,
        "elapsed_ms": 36.34,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "label": "S3 record after actual local execution/tests and map reads",
      "exit_code": 0,
      "result": {
        "status": "RECORDED",
        "message": "RECORDED",
        "can_skip_repeated_analysis": false,
        "scope_id": "review-C/local-addition-only/student-demo-20261019",
        "evidence_hash": "cbc3925a989f8a8f5154e188657bb2ff50c9217b5439f615d4f31cbfd0adf5ed",
        "current_status": "仅验证临时本地加法与输出",
        "changed_paths": [],
        "changed_fields": [
          "manifest_or_scope"
        ],
        "observed_bytes": 1227,
        "elapsed_ms": 35.69,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "label": "S3 pure local observation unchanged",
      "exit_code": 0,
      "result": {
        "status": "UNCHANGED",
        "message": "无变化",
        "can_skip_repeated_analysis": true,
        "scope_id": "review-C/local-addition-only/student-demo-20261019",
        "evidence_hash": "cbc3925a989f8a8f5154e188657bb2ff50c9217b5439f615d4f31cbfd0adf5ed",
        "current_status": "仅验证临时本地加法与输出",
        "changed_paths": [],
        "changed_fields": [],
        "observed_bytes": 1227,
        "elapsed_ms": 32.92,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "label": "S3 same size and mtime but changed content",
      "exit_code": 1,
      "result": {
        "status": "CHANGED",
        "message": "CHANGED",
        "can_skip_repeated_analysis": false,
        "scope_id": "review-C/local-addition-only/student-demo-20261019",
        "evidence_hash": "d92e45488c701a2d7251b9578186d21bbf54a5124ba2488a7dd24079731a2ab0",
        "current_status": "仅验证临时本地加法与输出",
        "changed_paths": [
          "report.md"
        ],
        "changed_fields": [
          "report"
        ],
        "observed_bytes": 1227,
        "elapsed_ms": 27.95,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "label": "S3 repeated changed check does not advance baseline",
      "exit_code": 1,
      "result": {
        "status": "CHANGED",
        "message": "CHANGED",
        "can_skip_repeated_analysis": false,
        "scope_id": "review-C/local-addition-only/student-demo-20261019",
        "evidence_hash": "d92e45488c701a2d7251b9578186d21bbf54a5124ba2488a7dd24079731a2ab0",
        "current_status": "仅验证临时本地加法与输出",
        "changed_paths": [
          "report.md"
        ],
        "changed_fields": [
          "report"
        ],
        "observed_bytes": 1227,
        "elapsed_ms": 20.83,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "label": "S3 after restore original baseline matches",
      "exit_code": 0,
      "result": {
        "status": "UNCHANGED",
        "message": "无变化",
        "can_skip_repeated_analysis": true,
        "scope_id": "review-C/local-addition-only/student-demo-20261019",
        "evidence_hash": "cbc3925a989f8a8f5154e188657bb2ff50c9217b5439f615d4f31cbfd0adf5ed",
        "current_status": "仅验证临时本地加法与输出",
        "changed_paths": [],
        "changed_fields": [],
        "observed_bytes": 1227,
        "elapsed_ms": 40.31,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "label": "S3 damaged baseline must fall back",
      "exit_code": 2,
      "result": {
        "status": "UNKNOWN",
        "can_skip_repeated_analysis": false,
        "reason": "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
        "fallback": "use normal targeted reads and required validation"
      }
    },
    {
      "label": "S3 corruption preserved; no reset or record attempted",
      "passed": true
    },
    {
      "label": "S3 small one-off edit bypass",
      "judgment": "Bypass skill per SKILL.md:12; no map/hash/record needed; not automatically measurable in a CLI."
    },
    {
      "label": "S1 explicit new rerun instruction honored despite old hashes: actual fresh calc invocation",
      "time_utc": "2026-10-18T17:52:22.402759+00:00",
      "exit_code": 0,
      "stdout": "{\"left\": 3, \"right\": 5, \"sum\": 8}\n",
      "baseline_untouched": true,
      "scope_note": "Actual arithmetic rerun only; screenshot/process/platform remain unverified; no baseline repair/advance."
    }
  ]
}
```

## 冻结文件收口校验

```json
[
  {
    "path": "SKILL.md",
    "sha256": "279C4C4BD8ED8D9549E7B9708D7430356BCFA6A8A591EA0365B46A07B71D9529",
    "match": true
  },
  {
    "path": "agents\\openai.yaml",
    "sha256": "8E569B9E7446065919211A68DF83751F58EDA04FED315C090C2854524ECE4CA2",
    "match": true
  },
  {
    "path": "assets\\manifest.example.json",
    "sha256": "96FCEF8B11FABEEE56FF92E4971C0A0565CB1F315202C5A9E5A620784D9D3D64",
    "match": true
  },
  {
    "path": "assets\\maps.md",
    "sha256": "54877450A46A6C95BDC827A147FF16D42EECB422C3059775C1F1FC6F9D3B30DA",
    "match": true
  },
  {
    "path": "references\\operation.md",
    "sha256": "82798BDB5D589C78F59B4BB669E3C06A63EC5F21D3C8570444E8C09137B7891B",
    "match": true
  },
  {
    "path": "scripts\\context_snapshot.py",
    "sha256": "D7460338940F3ED70095EDAFBEF084464CE0CDB0742A7DA497DAFB9AEC272D4D",
    "match": true
  },
  {
    "path": "tests\\test_context_snapshot.py",
    "sha256": "5EDD8635A02DADB25DA821580F86FB08DE8FE96BB07FE5BF64FBC2D2CFE3770D",
    "match": true
  }
]
```


# r2 变更范围独立复核（追加，保留 r1 原意见）

结论：**PASS（仅 r2 变更范围）**。未发现本轮目录保护阻断普通文件保存、读写或在退出后残留锁；对受保护目录本身的改名/删除限制确实存在，新增操作说明已明确限定。不承诺所有程序、所有文件系统和性能完全无影响。

真实代理仍为 `/root/workflow_review`。输入 `frozen-r2`，哈希清单 `frozen-r2-hashes.json`，初读/收口均 7/7 匹配；未读其他评审。本节只追加，不修改 r1 原意见。本次读取前的 reviewer-C.md SHA256 为 `b5d8617dc2657b570043c257ac67cbe35d2459a8fbf24a9bfdb6cff335c56e22`，追加后核对原字节前缀完全一致。

## 复核标准与变更定位

- Windows 新增真实 ChangeTime 校验必须阻止观察途中写入后恢复 mtime 的静默通过；不能通过独占文件写锁阻止正常任务写入。
- record 写入必须限缓存内；禁止缓存/祖先目录在写入中被改名或替换，退出正常/异常均释放句柄。普通文件写入、原子保存、未固定的子目录操作仍须可用。
- 固定目录只覆盖一次主动 record，不延长成后台服务或持续锁；目录正在重组、路径不支持或无法固定时应放弃优化，不能提权、重试等待或改领域任务。

原证据：`frozen-r2/SKILL.md:35`（record 仅本地 Windows）；`frozen-r2/references/operation.md:25`（ChangeTime、固定目录边界、普通读写、不重组时 record、UNKNOWN 回退）；`frozen-r2/scripts/context_snapshot.py:37-100`（标准库 ctypes、共享模式与 ExitStack 释放）、`140-168`（读取前后 stamp）、`220-224`（整次观察复查）、`318-320`（只在 record 固定目录）、`330-336`（异常 UNKNOWN，无提权/重试）。

与 r1 的差异只包含 SKILL/operation 说明、Windows API/ChangeTime/目录固定和 3 个对应测试；地图模板、manifest 模板、代理说明未变。不重跑 r1 无关场景，r1 保护内容/记忆/小任务旁路意见只适用于其原冻结版本，相关条款在 r2 未改。

## 真实执行结果

运行 r2 新增 3 个测试，无跳过：

1. `test_write_after_read_with_restored_mtime_is_unknown`：读取完成后写入并恢复 mtime，实际抛 Unknown，未误报无变化。
2. `test_cache_swap_before_record_never_writes_outside`：缓存目录改名在固定期间被拒绝，外部目录保持空；没有走到链接写出。
3. `test_directory_pin_allows_writes_and_releases`：固定期间普通文件写入仍可用；结束后缓存目录可以改名。

另外独立编写临时验证：在固定 cache 与所有祖先期间，分别在项目根和 cache 创建、写入、os.replace 原子替换已有文件，创建/改名/删除普通子目录，全部成功；另起短时同步子进程写入已有 report.txt 并读取，成功。尝试改名固定的 cache 和项目根均得到 WinError 32，与所声称的防替换边界一致；退出后两个目录均可改名，受控异常退出后也可改名。

最后真实 CLI record=`RECORDED/0`（37.29 ms），check=`UNCHANGED/0`（25.97 ms）；没有遗留 .state.lock 或 .state-*.tmp。受控固定区间为 115.68 ms，包含测试启动子进程的时间，不能当成正常 record 负担或 2 秒严格上限。

临时来源：`C:\Users\zbh\AppData\Local\Temp\context-budget-review-C-r2-0f40b1f786e5488299eea14babb0bac9/review_r2.py` 与同目录 results.json。完整结果附后。

## 原始意见、严重性与复验

| 发现 | 严重性/结论 | 改法 | 复验 |
| --- | --- | --- | --- |
| 无新增必改缺陷 | PASS | 当前 r2 无需强制改动 | 后续改共享模式/句柄范围时重跑上述 3 测试与普通原子保存验证 |
| record 期间固定 cache 及全部祖先目录本身不能被改名/删除 | 明确且已披露的能力边界；非普通文件写锁 | 保持 operation 的“正在重组目录时不 record”；运行中的重组或权限不足直接退回正常流程，不重试/提权 | 检查触发失败为 UNKNOWN，且句柄退出即释放；真实目录重组流程后续如使用需单独核验 |
| 新增 API 查询与目录句柄增加开销 | 未发现明显问题；未做代表性量化 | 不宣称性能无损；保留小任务旁路及按需 record，不能每次文件变化立即 record | 仅未来要宣称收益时测真实任务端到端时间，无需为本轮装依赖/平台 |

ChangeTime 的实际观察使用共享读/写/删除（share=7），固定目录用共享读/写（share=3），没有对输入文件建立拒写锁；不过工具无法保证第三方程序自身的独占分享模式兼容，无法读取时应走现有 UNKNOWN 回退。新代码没有安装环境、网络、模型、记忆写入或后台启动路径。

## 未验证边界

没有测试各版本 Windows、FAT/外接磁盘、映射网络盘真实连接、云占位符、杀进程/断电、所有第三方编辑器的保存协议；未针对所有对抗竞态做穷尽安全证明。只验证了当前 Windows/Python 3.14 本地临时目录。没有更改或读取全局记忆，没有验证 Git 发布状态。r2 的 record 仅 Windows 是主动限制，其他系统按文档停用该优化继续原流程，不把缓存无法建立当成原任务失败。

## r2 原始运行证据

```json
{
  "unit_tests": {
    "run": 3,
    "failures": 0,
    "errors": 0,
    "skipped": 0,
    "raw": "test_write_after_read_with_restored_mtime_is_unknown (r2_tests.SnapshotTests.test_write_after_read_with_restored_mtime_is_unknown) ... ok\ntest_cache_swap_before_record_never_writes_outside (r2_tests.SnapshotTests.test_cache_swap_before_record_never_writes_outside) ... ok\ntest_directory_pin_allows_writes_and_releases (r2_tests.SnapshotTests.test_directory_pin_allows_writes_and_releases) ... ok\n\n----------------------------------------------------------------------\nRan 3 tests in 0.297s\n\nOK\n"
  },
  "own_interference_checks": [
    {
      "folder": "C:\\Users\\zbh\\AppData\\Local\\Temp\\context-budget-review-C-r2-0f40b1f786e5488299eea14babb0bac9\\project",
      "create_write_atomic_replace_rename_child_dir": true
    },
    {
      "folder": "C:\\Users\\zbh\\AppData\\Local\\Temp\\context-budget-review-C-r2-0f40b1f786e5488299eea14babb0bac9\\project\\.context-cache",
      "create_write_atomic_replace_rename_child_dir": true
    },
    {
      "child_process_input_write": true,
      "stdout": "child process wrote\n"
    },
    {
      "pinned_directory_rename_denied": "C:\\Users\\zbh\\AppData\\Local\\Temp\\context-budget-review-C-r2-0f40b1f786e5488299eea14babb0bac9\\project\\.context-cache",
      "winerror": 32
    },
    {
      "pinned_directory_rename_denied": "C:\\Users\\zbh\\AppData\\Local\\Temp\\context-budget-review-C-r2-0f40b1f786e5488299eea14babb0bac9\\project",
      "winerror": 32
    },
    {
      "controlled_pin_held_ms": 115.68,
      "note": "includes child process startup; not production pin duration"
    },
    {
      "pinned_directories_renamable_after_normal_release": true
    },
    {
      "renamable_after_exception_release": true
    },
    {
      "command": "record",
      "exit_code": 0,
      "result": {
        "status": "RECORDED",
        "message": "RECORDED",
        "can_skip_repeated_analysis": false,
        "scope_id": "review-C-r2/local",
        "evidence_hash": "578d61846e81e4da87130f6892b1bbe04b1d25a70396207f9c256651b8e21fc1",
        "current_status": "actual ordinary-save validation completed",
        "changed_paths": [
          "report.txt"
        ],
        "changed_fields": [
          "manifest_or_scope",
          "report"
        ],
        "observed_bytes": 19,
        "elapsed_ms": 37.29,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "command": "check",
      "exit_code": 0,
      "result": {
        "status": "UNCHANGED",
        "message": "无变化",
        "can_skip_repeated_analysis": true,
        "scope_id": "review-C-r2/local",
        "evidence_hash": "578d61846e81e4da87130f6892b1bbe04b1d25a70396207f9c256651b8e21fc1",
        "current_status": "actual ordinary-save validation completed",
        "changed_paths": [],
        "changed_fields": [],
        "observed_bytes": 19,
        "elapsed_ms": 25.97,
        "coverage": "explicit_files_only; no domain or external verification"
      }
    },
    {
      "no_stale_lock_or_temp_after_cli": true
    }
  ],
  "temp_root": "C:\\Users\\zbh\\AppData\\Local\\Temp\\context-budget-review-C-r2-0f40b1f786e5488299eea14babb0bac9",
  "python": "3.14.0 (tags/v3.14.0:ebf955d, Oct  7 2025, 10:15:03) [MSC v.1944 64 bit (AMD64)]"
}
```

## r2 冻结收口哈希

```json
[
  {
    "path": "SKILL.md",
    "sha256": "A25B6CD8349E2E9E9A50BCF02CED8EEFEDDD8429B9EC3B3C488DAB99830FFBA9",
    "match": true
  },
  {
    "path": "agents\\openai.yaml",
    "sha256": "8E569B9E7446065919211A68DF83751F58EDA04FED315C090C2854524ECE4CA2",
    "match": true
  },
  {
    "path": "assets\\manifest.example.json",
    "sha256": "96FCEF8B11FABEEE56FF92E4971C0A0565CB1F315202C5A9E5A620784D9D3D64",
    "match": true
  },
  {
    "path": "assets\\maps.md",
    "sha256": "54877450A46A6C95BDC827A147FF16D42EECB422C3059775C1F1FC6F9D3B30DA",
    "match": true
  },
  {
    "path": "references\\operation.md",
    "sha256": "243F5108A6C4FC44445C892F5EB370B58F2E538382137913525700568D1CF4FB",
    "match": true
  },
  {
    "path": "scripts\\context_snapshot.py",
    "sha256": "9502A394F691C2F85D24B76A2C522182C8D007178B9FBC46C712A782FCC9D853",
    "match": true
  },
  {
    "path": "tests\\test_context_snapshot.py",
    "sha256": "6CDAE8B06F563A4872C2C01566049D297B2EB2E958AC2B7B1C8B498D209072F6",
    "match": true
  }
]
```
