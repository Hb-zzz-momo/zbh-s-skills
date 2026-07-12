---
name: ppt-data-storytelling-zh
description: "PPT 数据叙事与图表规格技能：根据比较、趋势、分布、关系、组成和不确定性选择图表，建立原始数据到指标、结论、视觉编码和来源的映射，检查坐标轴、统计口径、方向与误导风险，输出结论先行的 chart-spec.json。Use when: 科研答辩、数学建模PPT、商业数据汇报、图表选型、数据故事、图表误导检查、chart-spec.json。"
---

# PPT 数据叙事
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 边界

只处理数据页的口径、结论、图表选择和完整性。不要修改原始数据，不代替统计分析生成显著性结论，不代替构建器写 PPTX。

## Step 1：锁定数据口径

记录数据文件、sheet/range、字段、单位、时间范围、过滤规则、缺失值、聚合方法、指标方向和版本哈希。无法追溯的数据不得进入正式图表。

## Step 2：先写结论

每张图先写一句受数据支持的结论，再选择图表。区分描述、关联、因果、推断和建议；不得把相关写成因果。

## Step 3：选择图表

按 `references/chart-selection.md` 匹配任务：

- 比较：条形图、点图。
- 趋势：折线图、斜率图。
- 分布：直方图、箱线图、ECDF。
- 关系：散点图；必要时呈现区间。
- 组成：堆叠条形图；谨慎使用饼图。
- 不确定性：误差线、置信区间带或分布图。

## Step 4：建立 Chart Spec

使用 `assets/chart-spec-template.json`，明确数据源、x/y、系列、单位、轴起点、排序、颜色、标签、统计说明、来源和风险。

CSV 数据可用脚本生成可执行规格：

```powershell
python scripts/build_chart_spec.py --input data.csv --category quarter --value value --aggregate sum --title "季度结果" --unit "%" --source-id SRC-DATA --output chart-spec.json
```

输出同时保存输入绝对路径、SHA-256、字段、聚合、行数和轴口径，由 `pptx-builder-zh` 直接生成原生 PowerPoint 图表。

## Step 5：完整性 Gate

按 `references/data-integrity.md` 检查：

- 指标方向、样本量、单位与正文一致。
- 坐标轴截断、双轴、面积编码和颜色没有误导。
- 均值、方差、区间、P 值和效应量表述匹配分析方法。
- 图表仅使用真实数据；示例数据必须醒目标记。

## 输出

- `chart-spec.json`
- 数据源—指标—图表映射表
- 误导风险与未决口径清单

图表构建完成后切换 `ppt-render-qa-zh` 检查标签可读性和跨页一致性。

## 资源

- 图表选择：`references/chart-selection.md`
- 图表样式：`references/chart-styling.md`
- 数据完整性：`references/data-integrity.md`
