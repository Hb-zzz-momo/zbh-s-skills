# 工作流状态机与人工门禁

## 状态文件

在目标项目的 `软件著作权申请资料/workflow-state.json` 保存进度。每完成一个阶段立即原子更新；恢复时读取该文件，从第一个未通过阶段继续，不重做已确认阶段。

阶段推进使用 `check_environment.py --advance-stage <stage> --evidence <relative-path>`；需要人工门禁的阶段必须加 `--confirm`。截图阶段同时传 `--screenshot-method`，正式生成阶段同时传 `--confirm --authorize-formal-generation`。CLI 只允许推进 `current_stage`，验证证据属于该阶段且文件非空，并原子更新状态。事实或文件变化时运行 `--invalidate-from <stage>`，该阶段及全部下游重置为 `pending`，相关确认、截图方式和正式授权同步失效。

```json
{
  "schema_version": 1,
  "mode": "A|B|C|D",
  "project_root": "",
  "current_stage": "environment",
  "stages": {
    "environment": {"status": "pending|pass|caution|block", "evidence": ["00-项目证据/environment-check.json"], "confirmed_by_user": false}
  },
  "confirmations": {
    "project": false,
    "business": false,
    "application_fields": false,
    "code_selection": false,
    "screenshot_method": false,
    "markdown_bundle": false
  },
  "screenshot_method": "browser|desktop|user|skip|null",
  "formal_generation_authorized": false,
  "updated_at": "ISO-8601"
}
```

状态对象必须包含且类型正确的 9 个顶层键：`schema_version`、`mode`、`project_root`、`current_stage`、`stages`、`confirmations`、`screenshot_method`、`formal_generation_authorized`、`updated_at`。其中 `project_root` 与 `updated_at` 为非空字符串，`current_stage` 必须是阶段表中的一个键，`screenshot_method` 只能是 `browser|desktop|user|skip|null`，正式生成授权必须为布尔值。

`stages` 必须恰好包含下表 11 个阶段，不得缺失或增加键；每阶段必须含合法 `status`、字符串数组 `evidence` 与布尔值 `confirmed_by_user`。`confirmations` 必须恰好包含示例中的 6 个确认键且值均为布尔值。这里的“恰好”用于阻止旧版、裁剪或意外扩展状态绕过门禁。

初始化使用：

```powershell
python scripts/check_environment.py <项目根目录> --initialize
```

建议同时传 `--mode A|B|C|D`。既有状态的 `mode=null` 可由后续显式模式原子补齐；既有非空模式与新请求冲突时必须保留原状态并阻断，不能静默切换任务模式。

## 阶段顺序

| 阶段 | 必需输入 | 放行证据 | 阻断条件 |
| --- | --- | --- | --- |
| `environment` | 项目根、Python 环境 | 环境 JSON、输出目录可写 | 根目录不存在、输出越界 |
| `project` | 候选项目目录 | 唯一项目路径、用户确认 | 多候选未选择 |
| `readiness` | 可运行性、核心闭环、许可与源码 | READY/CONDITIONAL/BLOCK 报告 | 空壳、不可运行、权属或许可风险未处理 |
| `business` | 项目分析、README/PRD、源码证据 | 业务理解 MD/JSON、用户确认 | 业务定位或功能边界未确认 |
| `application-fields` | 业务理解、用户事实信息 | 字段 MD/JSON、验证报告、用户确认 | 必填缺失、敏感事实被猜测 |
| `code-selection` | source manifest、候选清单 | 用户确认的选择 JSON | 第三方/生成文件、越界路径、未确认 |
| `screenshot-method` | 可用工具与用户选择 | 方法、计划和采集规则 | 未选择方法；自动方式不可用却继续 |
| `markdown-draft` | 已确认业务/字段/代码、截图计划 | 全部草稿及自检、一次整体确认 | unsupported 功能、占位缺口未记录 |
| `formal-generation` | `markdown_bundle=true` | 用户授权、正式 DOCX/TXT | 未整体确认或敏感信息将进入公开路径 |
| `render-validation` | 正式 DOCX、渲染工具 | render/consistency/provenance 报告 | 未渲染却声称视觉 PASS |
| `final-review` | 全部报告和 output manifest | final checklist | 截图缺失、错误未清零、来源不一致 |

## 人工门禁

1. **项目门禁**：多个候选目录时停止，让用户选择唯一根目录。
2. **业务门禁**：用户确认定位、行业、目标用户、核心功能、典型流程和禁止写入的功能。
3. **申请字段门禁**：用户确认软件全称、简称、版本、著作权人、日期、开发方式、发表状态、环境、语言、权利范围和取得方式。证件号、日期、权利人和权属关系不得自动确定。
4. **代码门禁**：先生成候选清单和理由；只有确认后的文件/行段可进入材料。
5. **截图门禁**：用户选择浏览器自动、桌面自动、用户自行或跳过。自动方式必须先验证工具可用。
6. **正式生成门禁**：所有 Markdown 草稿只做一次整体确认。确认前不得生成正式 DOCX/TXT。

选择 `skip` 时允许完成草稿和经用户授权的预览版正式文件，但 `final-review` 必须为 `BLOCK`，并在正式输出清单写明“未达到最终提交状态：截图尚未补齐”。

## 转换规则

- `pass`：证据完整，进入下一阶段。
- `caution`：只允许补证据、生成草稿或低风险审计，不允许宣称最终可提交。
- `block`：停止下游阶段，只能修复、补问或恢复。
- 阶段不能跳跃；`current_stage` 必须等于首个非 `pass` 阶段，任一未通过阶段之后不得出现 `pass`；`updated_at` 必须为合法 ISO-8601。回退时保留旧产物并通过 `--invalidate-from` 重置状态。
- `formal_generation_authorized=true` 只由用户整体确认产生，不能由脚本推断。
- 任一确认后的事实发生变化，应使所有下游阶段回到 `pending` 并重新校验。
- 每个标记为 `pass` 的非最终阶段都必须记录一个或多个相对材料根的现存证据文件；空 evidence 不能通过最终校验。
- 运行 `validate_outputs.py` 前，`final-review` 可以是 `pending|caution|block`；脚本重新计算全部门禁后，原子写回最终状态及 `final-checklist.md`、`output-manifest.json` 证据，避免“先手工标 pass 才能验证”的循环。

## 恢复流程

1. 读取状态文件并验证 JSON。
2. 核对项目根和已记录证据文件仍存在，必要时复算哈希。
3. 找到第一个不是 `pass` 的阶段；若上游证据变化，从受影响阶段回退。
4. 展示已确认事项和待办，不重复询问未变化的内容。
5. 状态文件损坏，或虽能解析但缺阶段、缺确认键、缺必要顶层键、类型错误时，先保留原字节为 `04-校验报告/workflow-state.corrupt-<timestamp>-<sha256>.bak`，再创建 `04-校验报告/workflow-recovery-report.json`，记录原文件路径与哈希、损坏原因、可复用证据、重建字段、回退阶段和执行时间；由现有产物保守重建新状态，所有发现的阶段最多恢复为 `caution`，全部人工确认与正式生成授权重置为 `false`。恢复命令整体返回 `CAUTION`，不得让缺失阶段延迟到下游并触发 `KeyError`。
