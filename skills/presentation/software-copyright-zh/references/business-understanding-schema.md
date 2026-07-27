# 业务理解 Schema

业务理解必须由模型阅读真实项目证据后填写。脚本只能扫描文件、入口、路由、源码统计和候选证据，不得根据关键词表自动决定行业、核心价值或功能结构。

## JSON 契约

```json
{
  "schema_version": 1,
  "software_name": "",
  "product_positioning": "",
  "industry": "",
  "target_users": [],
  "core_value": [],
  "business_features": [
    {
      "feature_name": "",
      "description": "",
      "evidence_ids": [],
      "confidence": "confirmed|partial|unsupported"
    }
  ],
  "operation_flows": [],
  "page_modules": [],
  "manual_modules": [
    {
      "title": "",
      "purpose": "",
      "entry": "",
      "visible_elements": [],
      "user_actions": [],
      "input_or_state_rules": [],
      "error_feedback": [],
      "result_feedback": [],
      "evidence_ids": [],
      "screenshot_ids": []
    }
  ],
  "application_purpose": "",
  "main_functions": "",
  "technical_characteristics": "",
  "system_requirements": {},
  "evidence_sources": [],
  "excluded_features": [],
  "user_confirmed": false,
  "confirmed_at": null
}
```

## 证据规则

`00-项目证据/source-evidence-map.json` 使用独立的功能证据契约：

```json
{
  "schema_version": 1,
  "features": [
    {
      "feature_id": "",
      "feature_name": "",
      "description": "",
      "evidence_files": [],
      "routes": [],
      "api_endpoints": [],
      "screenshots": [],
      "confidence": "confirmed|partial|unsupported"
    }
  ]
}
```

- `evidence_sources` 只能引用项目内 README、PRD、路由、页面、组件、接口、模型、测试或用户正式说明。
- 每个 `business_features` 和 `manual_modules` 至少关联一个 `source-evidence-map.json` 证据 ID。
- 每个 `confidence=confirmed` 功能的 `evidence_files` 必须是 `source-manifest.json` 内的路径，并至少有一条被用户确认入选 `代码文件选择.json`；同时必须关联真实存在的截图，且功能名称出现在正式材料中。manifest、入选源码、真实截图或正式材料任一端未闭合即为 `BLOCK`。
- `unsupported` 功能必须进入 `excluded_features`，禁止进入申请表、手册和截图清单。
- `partial` 功能只能进入待确认草稿，用户确认或补证据前不得进入正式材料。
- 外部行业资料只能标为 `industry_reference`，不能证明项目具备某功能。

## 业务确认清单

- 软件定位与面向行业是否准确。
- 目标用户和典型操作流程是否真实。
- 核心功能是否都能追溯到项目证据。
- 哪些未完成、实验性或内部功能不得写入。
- 手册模块是否对应真实页面或可执行流程。

`user_confirmed=false` 时，申请字段、操作手册和正式材料阶段全部阻断。
