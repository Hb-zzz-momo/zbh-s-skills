# 定向检索手册

## 目录

1. 搜索前任务标签
2. 查询公式
3. 各来源查询策略
4. 案例检查
5. 数量与停止条件
6. 失败与降级

## 1. 搜索前任务标签

先写一行：

```text
交付物：[类型]；受众：[人群]；行业：[主题]；风格：[约束]；重点：[维度]；不可改变：[边界]
```

缺少交付物、受众或不可改变项时，先读取项目材料或向用户确认。

## 2. 查询公式

使用：

```text
行业或主题 + 交付物类型 + 页面/模块 + 目标风格 + 关键功能
```

避免 `beautiful website`、`good PPT`、`dashboard design`、`coding prompt` 等宽泛词。

示例：

- `open source analytics SaaS landing page repository network visualization`
- `AI developer tools dashboard risk alerts empty state`
- `university data science defense presentation full deck`
- `Flask Vue 3 Codex project skill tools acceptance criteria`
- `multi-objective feature selection mechanism diagram paper`

## 3. 各来源查询策略

| 来源类别 | 查询重点 |
|---|---|
| 完整 Web 案例 | 行业 + 首页/产品页 + 结构/功能 |
| 产品 UI / 流程 | 产品类型 + 动作 + 平台 + 状态 |
| PPT / Deck | 主题 + presentation/deck + 完整项目/多页 |
| 图表 | 数据关系 + chart type + labels/interaction |
| Coding Prompt | 产品/模型 + 官方文档主题 + 工具/约束/评估 |
| 科研图 | 学科/算法 + mechanism/schematic + paper/figure |
| 架构图 | 平台/工作负载 + reference architecture + data flow/security |
| 配色/字体 | 行业 + mood + accessibility/deployment font |

同一搜索词不得机械复制到所有网站；用网站擅长的页面类型和关键词改写。

## 4. 案例检查

打开具体案例后记录：

- 页面/Deck/图示是否完整，还是只有封面或缩略图。
- 结构、层级、留白、字体、颜色、状态、数据标签和响应式。
- 与当前行业、受众、技术栈和内容是否匹配。
- 可迁移规律与不适合直接采用的部分。
- 是否涉及模板、字体、图标、插画、代码或品牌资产；记录许可。

只能读取文本摘要时，写明“未完成完整视觉检查”，结果最高 `CAUTION`。

## 5. 数量与停止条件

普通任务：网站 2–5 个、具体案例 3–8 个、核心参考 2–4 个、可执行规律 3–7 条。

大型任务只在新来源补充新维度时扩展。连续两个案例没有带来新的结构、视觉、交互、图表或事实信息时停止检索。

## 6. 失败与降级

| 场景 | 动作 | 状态上限 |
|---|---|---|
| 无法联网 | 使用本地截图、模板、设计规范和历史案例；明确“实时参考检索未完成” | CAUTION |
| 单个网站不可达 | 选择同类别替代来源并记录原因 | PASS（若仍满足证据） |
| 结果不匹配 | 加行业、页面、功能或风格词；更换来源 | CAUTION，直至补足 |
| 只有首页/摘要 | 继续打开具体案例；无法打开则明确限制 | CAUTION |
| 用户要求快速 | 两个互补来源 + 三条规律 + 落实记录 | PASS（若证据完整） |
| 用户禁止联网 | 不访问外部网站，只用用户/项目材料 | CAUTION 或按用户验收边界 |
