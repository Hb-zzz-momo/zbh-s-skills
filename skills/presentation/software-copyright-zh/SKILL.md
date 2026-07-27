---
name: software-copyright-zh
description: "软件著作权申请材料全流程 Skill：从真实项目执行准备度审计、证据采集、业务理解、申请表字段确认、源码候选与哈希追溯、用户操作手册、真实截图、Markdown 草稿、正式 DOCX/TXT、渲染一致性校验和提交清单；也可审计并保守修复已有软著材料。Use when: 软著, 软件著作权, 软著申请, 申请表信息, 操作手册, 用户手册, 源码鉴别材料, 前30页, 后30页, 源程序量, 软著材料审计。代码和功能必须来自用户确认的真实项目，主要交付物为证据 JSON、草稿、正式资料与校验报告。不适用于与软著无关的普通项目开发，也不单独承担从零项目开发。"
---

# 软件著作权申请材料工作流

## 技能目标

从真实项目生成可追溯、无编造、字段一致、源码真实且可由申请人最终检查的申请材料。不得承诺“包过”“保证下证”或“百分之百通过审核”。

## 任务模式

| 模式 | 触发条件 | 执行边界 |
| --- | --- | --- |
| A 已有项目生成材料 | 项目已存在，需要申请表、手册、截图或源码材料 | 不重构、不补功能；未实现或 `unsupported` 功能不得进入正式材料 |
| B 已有材料审计与修复 | 已有手册、代码材料或申请表，需要核查/修复 | 先备份，列问题与原因；只改用户授权内容，不承诺审核结论 |
| C 项目准备度审计 | 项目尚不确定是否适合生成材料 | 检查可运行性、核心闭环、真实源码、空壳页、截图状态、名称/版本、第三方与许可证；输出 READY/CONDITIONAL/BLOCK |
| D 为申报准备新项目 | 用户明确要求从零开发 | 严格按 `project-structure-architect` → `engineering-skill-flow-zh` → `software-copyright-zh` 路由；先完成真实开发与业务闭环，再进入材料阶段 |

严格按用户材料生成时，先使用 `plan-faithful-execution-zh`。需要真实浏览器截图时阶段性使用 `browser-testing-with-devtools`；需要正式 Word 生成或格式修复时调用对应文档生成/格式检查能力；最终产物整理按需使用 `artifact-curator-zh`。每阶段只加载一个主 Skill 和最多两个必要辅助 Skill。

## 开始门禁

运行脚本要求 Python 3.10+；先用 `python --version` 确认解释器，再执行环境检查。脚本不会自动安装依赖。

1. 只要本轮将初始化、补建或重组 `软件著作权申请资料/` 多文件树，必须先使用 `project-structure-architect`，读取目标项目适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定资料树的唯一合理路径；结构门禁未 `PASS` 前不得执行 `--initialize`。纯只读审计且不创建、移动文件时不重复触发。
2. 读取目标项目 README/PRD、构建清单和现有材料。
3. 多个项目候选时停止，让用户选择；不得猜测项目根。
4. 读取[官方要求与证据分层](references/official-requirements-and-evidence.md)和[状态机](references/workflow-state-machine.md)。当前登记页面未核验时明确标为 `CAUTION`。
5. 结构门禁通过后运行环境检查；只生成草稿也必须建立状态文件：

```powershell
$mode = "C"  # 按上表替换为 A、B、C 或 D
python "<skill>/scripts/check_environment.py" "<项目根>" --initialize --mode $mode
```

6. 模式 B 先运行只读备份审计；脚本不修改原件，任何修复仍需用户另行授权：

```powershell
python "<skill>/scripts/validate_outputs.py" "<资料>" --project-root "<项目根>" --audit-existing "<现有材料文件或目录>"
```

脚本写入带时间戳和 SHA-256 的只读备份及不可变审计报告。用户授权修复后，按初始报告的文件哈希建立 `repair-ledger.json`，再使用 `--repair-ledger` 复验；未登记改动、前后哈希不符或未复验均为 `BLOCK`。模式 D 在真实业务闭环完成前不得进入材料阶段。

每完成一个阶段，使用同一环境 CLI 原子推进状态；不得手改全阶段为 `pass`：

```powershell
python "<skill>/scripts/check_environment.py" "<项目根>" --advance-stage project --confirm `
  --evidence "00-项目证据/project-analysis.json" `
  --evidence "00-项目证据/source-manifest.json" `
  --evidence "00-项目证据/source-line-count.json"
```

上游事实变化时使用 `--invalidate-from <阶段>` 级联回退；`formal-generation` 还必须显式传入 `--confirm --authorize-formal-generation`。

## 输出目录

默认只在目标项目内创建：

```text
软件著作权申请资料/
├── workflow-state.json
├── 00-项目证据/
│   ├── environment-check.json
│   ├── project-analysis.json
│   ├── source-line-count.json
│   ├── source-evidence-map.json
│   └── source-manifest.json
├── 01-草稿/
│   ├── 业务理解.md
│   ├── 业务理解.json
│   ├── 申请表信息.md
│   ├── 申请表信息.json
│   ├── 代码文件候选清单.md
│   ├── 代码文件选择.json
│   ├── 操作手册.md
│   └── 草稿自检记录.md
├── 02-截图/
│   ├── screenshot-plan.md
│   └── images/
├── 03-正式资料/
│   ├── 申请表信息.txt
│   ├── 软件全称_操作手册.docx
│   └── 软件全称_代码鉴别材料.docx
└── 04-校验报告/
    ├── consistency-report.md
    ├── provenance-report.md
    ├── render-report.md
    ├── final-checklist.md
    └── output-manifest.json
```

不得把正式 Word/TXT 散落到项目根，不得将含个人敏感信息的正式资料加入 Git。

模式 B 另写 `04-校验报告/material-audit-report.md` 记录原件哈希、问题、原因、授权修改与复验；模式 C 另写 `04-校验报告/readiness-report.md/json`，记录 READY/CONDITIONAL/BLOCK、逐项证据和进入下一阶段的条件。这些条件产物不替代正式材料树中的必选文件。

## 核心工作流

### 1. environment → project → readiness

运行项目分析和源码清单：

```powershell
python "<skill>/scripts/analyze_project.py" "<项目根>" --output "<资料>/00-项目证据/project-analysis.json"
python "<skill>/scripts/collect_source_manifest.py" "<项目根>" --output "<资料>/00-项目证据/source-manifest.json"
python "<skill>/scripts/count_source_lines.py" "<项目根>" --manifest "<资料>/00-项目证据/source-manifest.json" --output "<资料>/00-项目证据/source-line-count.json"
```

脚本未知技术栈时退化为通用扫描，不能据此失败或猜测业务。准备度必须基于真实启动/入口、核心闭环、源码与许可证证据判为 READY、CONDITIONAL 或 BLOCK。

模式 C 使用已实际执行的启动、核心流程与测试日志生成规定路径的双份报告；脚本不执行任意项目命令，也不接受只写“已运行”的口头记录：

```powershell
python "<skill>/scripts/analyze_project.py" "<项目根>" --readiness --runtime-evidence "<项目内runtime-evidence.json>" --output "<资料>/00-项目证据/project-analysis.json"
```

输出固定为 `<资料>/04-校验报告/readiness-report.json` 与 `.md`；缺少真实启动或核心流程证据时为 `BLOCK`，不得进入正式生成。
`runtime-evidence.json` 的 startup、core-flow、test 三类收据必须包含命令、项目内工作目录、起止时间、实际退出码、日志路径与日志 SHA-256；任一缺失、越界或哈希不符均为 `BLOCK`。截图属于后续阶段，不作为 readiness 前置条件。

### 2. business

模型阅读项目证据、必要源码和正式说明，按[业务理解 Schema](references/business-understanding-schema.md)生成 MD/JSON，并建立 `source-evidence-map.json`。每个功能映射页面/路由/组件/API/模型/测试/正式说明，置信度为 `confirmed|partial|unsupported`。用户确认定位、行业、用户、功能、流程和排除项后才能继续。

### 3. application-fields

按[申请字段 Schema](references/application-field-schema.md)生成建议值和来源。著作权人、证件信息、完成/发表日期、权属关系、取得方式和实际硬件环境不得自动确定。验证后让用户一次确认字段：

```powershell
python "<skill>/scripts/validate_application_fields.py" "<资料>/01-草稿/申请表信息.json"
```

正式校验时每个字段必须使用完整元数据 envelope；`03-正式资料/申请表信息.txt` 按 Schema 的固定字段顺序使用 `字段键<TAB>JSON值` 序列化，必须与已确认 JSON 逐字段一致。

### 4. code-selection

按[源码材料规则](references/code-material-rules.md)生成候选清单：

```powershell
python "<skill>/scripts/propose_code_selection.py" "<项目根>" --manifest "<资料>/00-项目证据/source-manifest.json" --json-output "<资料>/01-草稿/代码文件选择.json" --markdown-output "<资料>/01-草稿/代码文件候选清单.md"
```

用户确认路径和行段后方可生成材料。第三方、依赖、构建产物、生成文件、密钥、隐私和越界路径一律阻断。项目总行数、入选代码行数、Word 实际页数和法规页数分别记录，不使用“核心代码必须少于 3000 行”规则。

### 5. screenshot-method → markdown-draft

按[截图与渲染规则](references/screenshot-and-render-rules.md)让用户选择浏览器自动、桌面自动、用户自行或跳过；自动方式先验证工具。截图只能来自真实运行软件并记录采集元数据。

截图计划必须逐图记录 11 列元数据与 SHA-256；图片至少 320×200，且每张确认截图的原始字节必须嵌入正式操作手册 DOCX。`草稿自检记录.md` 必须记录 reviewer、ISO 时间及五项机器可读 `PASS`。

按[手册规则](references/manual-writing-rules.md)和[差异化规则](references/differentiation-rules.md)生成全部 Markdown 草稿。手册面向使用者，以自然段说明真实页面和操作；不得写成技术设计、固定字段模板或营销文案。草稿可记录缺失项，正式材料不得出现占位词。

完成草稿自检后只向用户发起一次整体确认，并把结果写入状态文件。未确认不得生成正式 DOCX/TXT。

### 6. formal-generation → render-validation → final-review

用户授权后，使用适用的本地文档生成能力把已确认草稿生成到 `03-正式资料/`，再运行：

```powershell
python "<skill>/scripts/validate_consistency.py" --application "<资料>/01-草稿/申请表信息.json" --materials-root "<资料>" --source-manifest "<资料>/00-项目证据/source-manifest.json" --selection "<资料>/01-草稿/代码文件选择.json" --evidence-map "<资料>/00-项目证据/source-evidence-map.json" --report "<资料>/04-校验报告/consistency-report.md" --provenance-report "<资料>/04-校验报告/provenance-report.md"
python "<skill>/scripts/validate_outputs.py" "<资料>"
```

正式 DOCX 必须转 PDF 或逐页图片检查页眉页脚、分页、代码截断、字体颜色、乱码、空白页、图片清晰度/裁切、标题孤行、页数、占位词、蓝色超链接和模板残留。无法渲染时写明未完成视觉校验，不得声称完全验收。

## 强制真实性与隐私规则

- 功能无 confirmed 证据不得进入正式材料。
- 代码只来自确认的真实文件；生成前后校验路径、行段和 SHA-256，不改写逻辑、不重复凑页。
- 截图只来自真实运行状态；设计稿和 AI 图不能冒充产品截图。
- 身份证号、统一社会信用代码、手机号、真实账号、密钥和私有地址不得进入 Git、fixture、README、日志、示例或公共审计报告。
- 正式材料若缺截图、字段确认、源码来源或渲染证据，最终状态必须是 `BLOCK` 或明确降级的 `CAUTION`。

## References 渐进加载

- 法规、当前页面与工作流约定：[official-requirements-and-evidence.md](references/official-requirements-and-evidence.md)
- 阶段、确认和恢复：[workflow-state-machine.md](references/workflow-state-machine.md)
- 业务与字段：[business-understanding-schema.md](references/business-understanding-schema.md)、[application-field-schema.md](references/application-field-schema.md)
- 源码与手册：[code-material-rules.md](references/code-material-rules.md)、[manual-writing-rules.md](references/manual-writing-rules.md)
- 截图、渲染与差异化：[screenshot-and-render-rules.md](references/screenshot-and-render-rules.md)、[differentiation-rules.md](references/differentiation-rules.md)
- 验收和上游：[quality-gates.md](references/quality-gates.md)、[upstream-attribution.md](references/upstream-attribution.md)

## 失败处理与验收

错误时脚本输出 UTF-8 JSON 和非零退出码；不得静默安装依赖、联网上传源码或读取项目外无关目录。状态文件损坏时保留原件并重建恢复报告，不从头覆盖。

最终按[质量门禁](references/quality-gates.md)检查名称、版本、字段、功能、源码、敏感信息、截图、渲染和 output manifest。只有所有必选项与证据闭环才是 `PASS`；非阻断风险为 `CAUTION`；任一必选实现、确认、测试或复现证据缺失为 `BLOCK`。
