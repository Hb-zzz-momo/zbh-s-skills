# 申请表字段 Schema

## 状态说明

本 Schema 用于采集、确认和一致性校验，不等于当前登记网站的已核验字段顺序。2026-07-12 无法直接访问登录后页面，当前页面状态见[官方要求与证据分层](official-requirements-and-evidence.md)。

## 通用字段模型

每个字段记录以下属性：

```json
{
  "value": null,
  "suggested_value": null,
  "data_type": "string|integer|array|date|enum|object",
  "required": true,
  "character_limit": null,
  "allowed_values": [],
  "source": "user|project|official-page|inference",
  "project_inferable": false,
  "user_confirmation_required": true,
  "confirmed": false,
  "verified_at": null
}
```

可推断字段只能写入 `suggested_value`；用户确认后必须显式复制到 `value`。在 `--require-confirmed` 正式校验中，`suggested_value` 永远不作为字段值，即使同一字段写了 `confirmed=true` 也会 `BLOCK`。未经当前官方页面核验的字符限制和枚举应为 `null` 或明确标为工作流建议。

## 字段清单

下表逐字段给出附件要求的元数据。`null` 表示当前登录后页面未取得，不能擅自填写数字限制；“工作流值”不是官网枚举。

| 键/中文名 | 类型 | 工作流必填 | 字符限制 | 允许值 | 来源 | 可由项目建议 | 必须用户确认 | 当前核验日期 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `software_full_name` 软件全称 | string | 是 | `null` | 页面待核验 | 项目名称候选 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 全套材料唯一名称源 |
| `software_short_name` 软件简称 | string/null | 否 | `null` | 页面待核验 | 项目简称候选 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 无简称也确认 `null` |
| `version` 版本号 | string | 是 | `null` | 页面待核验 | 项目版本候选 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 不自动改为 V1.0 |
| `software_category` 软件分类 | enum/string | 是 | `null` | 页面枚举待核验 | 当前表单 + 用户 | 否 | 是 | 页面未核验；2026-07-12 | 不复制旧模板枚举 |
| `copyright_holders` 著作权人 | array | 是 | `null` | 页面结构待核验 | 用户私有事实 | 否 | 是 | 页面未核验；2026-07-12 | 公共草稿只存名称/类型 |
| `development_completion_date` 开发完成日期 | date | 是 | `null` | `YYYY-MM-DD`（工作流格式） | 用户事实 | 否 | 是 | 页面未核验；2026-07-12 | 禁止按 Git 日期确定 |
| `development_method` 开发方式 | enum/string | 是 | `null` | 页面枚举待核验 | 用户/权属材料 | 否 | 是 | 页面未核验；2026-07-12 | 合作、委托等需证据 |
| `publication_status` 发表状态 | enum | 是 | `null` | `published|unpublished`（工作流值） | 用户事实 | 否 | 是 | 页面未核验；2026-07-12 | 页面显示值仍需映射核验 |
| `first_publication_date` 首次发表日期 | date/null | 条件必填 | `null` | `YYYY-MM-DD|null`（工作流格式） | 用户事实 | 否 | 是 | 页面未核验；2026-07-12 | 未发表必须为空 |
| `rights_scope` 权利范围 | enum/string | 是 | `null` | 页面枚举待核验 | 用户/权属材料 | 否 | 是 | 页面未核验；2026-07-12 | 不自动选择全部权利 |
| `rights_acquisition_method` 权利取得方式 | enum/string | 是 | `null` | 页面枚举待核验 | 用户/权属材料 | 否 | 是 | 页面未核验；2026-07-12 | 原始/继受等需确认 |
| `development_hardware` 开发硬件环境 | string | 是 | `null` | 页面待核验 | 用户事实 | 否 | 是 | 页面未核验；2026-07-12 | 不读取当前机器冒充 |
| `runtime_hardware` 运行硬件环境 | string | 是 | `null` | 页面待核验 | 项目部署证据 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 只能生成建议值 |
| `development_os` 开发操作系统 | string | 是 | `null` | 页面待核验 | 用户事实 | 否 | 是 | 页面未核验；2026-07-12 | 实际环境由用户确认 |
| `development_tools` 开发工具 | array/string | 是 | `null` | 页面待核验 | 构建清单 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 只列真实工具 |
| `runtime_platform` 运行平台/操作系统 | string | 是 | `null` | 页面待核验 | 部署/启动证据 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 结合真实部署确认 |
| `runtime_support` 运行支撑环境 | array/string | 是 | `null` | 页面待核验 | 依赖清单 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 只列真实依赖 |
| `programming_languages` 编程语言 | array | 是 | `null` | manifest 中实际语言 | source manifest + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 不按技术栈猜测 |
| `source_line_count` 全部源程序量 | integer | 是 | 不适用 | 非负整数 | source-line-count + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 与入选行数/页数分离 |
| `application_purpose` 开发目的 | string | 是 | `null` | 页面待核验 | 已确认业务理解 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 只写真实目的 |
| `industry` 面向领域/行业 | string | 是 | `null` | 页面待核验 | 用户事实 | 否 | 是 | 页面未核验；2026-07-12 | 脚本不得关键词推断 |
| `main_functions` 主要功能 | string | 是 | `null` | confirmed 功能 | 业务证据链 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 排除 partial/unsupported |
| `technical_characteristics` 技术特点 | string/array | 是 | `null` | 页面待核验 | 项目证据 + 用户 | 是 | 是 | 页面未核验；2026-07-12 | 不写营销口号 |

## 顶层 JSON

```json
{
  "schema_version": 1,
  "current_form_evidence": {
    "source_url": "https://register.ccopyright.com.cn/...",
    "verified_at": "YYYY-MM-DD",
    "form_version": "登录后表单版本或页面标识",
    "snapshot_path": "软件著作权申请资料/00-项目证据/official-form.html",
    "snapshot_sha256": "对 snapshot_path 当前字节复算的 64 位 SHA-256"
  },
  "fields": {},
  "confirmed_fields": [],
  "private_fields_path": null,
  "user_confirmed": false,
  "confirmed_at": null
}
```

`current_form_evidence` 必须是对象：`source_url` 仅接受 `https://register.ccopyright.com.cn`、`https://www.ccopyright.com.cn` 或 `https://ccopyright.com.cn` 下的官方页面；`verified_at` 必须是真实、非未来的 `YYYY-MM-DD`。`form_version` 只是辅助元数据，不能单独解除 `CAUTION`。要标记“当前在线表单已核验”，必须同时提供 `snapshot_path` 与 `snapshot_sha256`：快照必须是绑定项目根或材料根以内的非空可读文件，校验器会读取当前字节并复算 SHA-256；路径越界、文件不可读或哈希不符均为 `BLOCK`。只有 `official_form_verified_at` 日期、访问日期、口头说明或任意版本字符串不构成页面证据。

声明真实快照时还必须记录 `capture_method`、与 `verified_at` 同日的 `captured_at`、`page_title`、完整内部 `field_names` 映射及 `user_confirmed_source=true`；登录页不能作为字段快照，标题必须出现在快照字节中。机器校验只证明路径、内容和人工来源确认闭环，不替代申请人对页面真实性的责任。

正式校验要求每个字段使用完整 envelope，并使 `confirmed_fields` 与字段内 `confirmed` 一致。正式 TXT 固定为首行 `schema_version<TAB>1`，随后按本表顺序写 `字段键<TAB>JSON值`；缺字段、重复字段、解析失败或与 JSON 不一致均为 `BLOCK`。

## 敏感信息边界

证件号、身份证号、统一社会信用代码、手机号、地址等只允许写入申请人控制的本地正式资料私有文件，且不得进入 Git、测试 fixture、README、示例、日志或 `skill-outputs` 审计报告。公共草稿只记录 `private_fields_path` 和“是否已由用户补齐”，不记录值。

以下事实禁止自动确定：证件信息、开发完成日期、首次发表日期、权利取得方式、合作/委托关系和实际硬件环境。

## 校验规则

- 工作流必填字段缺失或未确认：`BLOCK`。
- `publication_status=unpublished` 但存在首次发表日期：`BLOCK`。
- `publication_status=published` 但缺首次发表日期：`BLOCK`。
- 日期必须为 `YYYY-MM-DD` 且为真实日历日期。
- `source_line_count` 为非负整数，只表示项目全部源程序量。
- `current_form_evidence` 缺失时标记 `CAUTION`；结构无效时标记 `BLOCK`。当前字段页面未核验时，最终状态最高为 `CAUTION`，不得声称“可直接提交”。
- `current_form_evidence` 只有版本标签但没有真实快照时标记 `CAUTION`；声明了快照但路径越界、不可读或 SHA-256 无法复算一致时标记 `BLOCK`。
- `user_confirmed=false` 时不得进入正式提交结论。
