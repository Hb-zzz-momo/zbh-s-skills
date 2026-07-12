# Reference Brief 模板

## Markdown 模板

```markdown
# Reference Brief

## 当前任务
- 交付物：
- 使用场景：
- 目标受众：
- 行业/主题：
- 技术栈/目标环境：
- 用户风格要求：
- 不可改变项：
- 参考维度：

## 参考分析

### 来源 1
- 参考来源：
- 具体案例或页面：
- URL：
- 适合当前任务的原因：
- 事实：
- 视觉/结构观察：
- 推断：
- 可借鉴元素：
- 不适合直接采用的元素：
- 向当前项目的转化方式：
- 许可证/使用条件：

### 来源 2
同上。

## 综合规律
1. [可执行规律]
2. [可执行规律]
3. [可执行规律]

## 当前项目落实
| 规律 | 页面/组件/图表/Prompt 字段/图形模块 | 实现方式 | 验收证据 |
|---|---|---|---|

## 明确不采用
- [模式]：原因。

## 限制
- 联网、视觉检查、许可或内容限制。
```

## JSON 模板

与 `scripts/reference_router.py validate-brief` 兼容：

```json
{
  "task": {
    "deliverable": "",
    "audience": "",
    "industry": ""
  },
  "design_goal": "",
  "reference_dimensions": ["结构", "视觉"],
  "live_access": true,
  "reviewed_case_count": 3,
  "reviewed_website_count": 2,
  "sources": [
    {
      "name": "",
      "url": "https://example.com/concrete-case",
      "case": "具体案例或页面名称",
      "relevance": "",
      "facts": ["来源明确陈述的事实"],
      "observations": [""],
      "inferences": ["基于观察形成、仍需验证的推断"],
      "adopt": [""],
      "reject": [""],
      "translation": [""],
      "license_checked": true
    }
  ],
  "rules": ["规则 1", "规则 2", "规则 3"],
  "rejected_patterns": ["不采用的模式及原因"],
  "applied_to_final": ["页面/组件/模块"],
  "limitations": [],
  "fact_observation_inference_separated": true
}
```

`reviewed_case_count` 记录实际检查的 3–8 个案例，`reviewed_website_count` 记录实际访问的 2–5 个网站；`sources` 只放最终保留的 2–4 个核心参考，不要混用三个数量口径。

离线降级时将单个来源的 `url` 改为 `path`，`reviewed_case_count` 为 1–8、`reviewed_website_count` 为 `0`，至少保留一个用户提供或项目内可靠材料，并在 `limitations` 中逐字记录“实时参考检索未完成”；完整性通过时状态最高为 `CAUTION`。

## 判定

- `PASS`：设计目标与参考维度明确，至少两个具体且互补来源、3–7 条规律、不采用模式、落实位置、许可与事实边界齐全。
- `CAUTION`：无法联网或视觉检查受限，但限制与替代证据明确。
- `BLOCK`：只有网站首页/名称、少于两个来源、无转译、无落实或许可不明。
