# OpenRank 架构图缺陷泛化复盘

## 这次为什么会漏检

之前的修复把用户截图中的问题当成了局部坐标问题，例如 SQLite 表格、Metric Ingestion、Fetch Data 标签、Frontend 底部迷你流程分别单独处理。虽然也做了全图巡检，但巡检粒度仍偏“区域级”，没有把一个缺陷升级为同类结构的全局规则。

核心失误是：看到“某个区块溢出”后，没有立即生成“全图所有紧凑卡片、表格行、连接标签、迷你流程都必须复查”的同类元素清单。因此后续仍可能在别的结构里出现同一种问题。

## 本图应采用的缺陷类型

- 文字溢出/贴边：所有小卡片、按钮、能力项、表格行、连接标签。
- 图标-文字碰撞：所有 icon + label 组合，包括数据库行、API 行、能力卡片和外部数据源列表。
- 重复行布局溢出：SQLite Database、REST APIs、Metric Ingestion、External Data Sources、Middleware/Services。
- 连接标签嵌入边框：REST API Requests、JSON Responses、Cached Data、Query/Read、Fetch Data 等模块间标签。
- 嵌套小流程拥挤：Frontend 底部 receives/renders 流程、Data Processing pipeline、capabilities 条带和 legend。
- 目标软件渲染错位：draw.io 原生可编辑文件、fixed-background drawio、SVG/PDF/PNG 导出效果。

## 后续修复必须执行的扫描

1. 为每一类紧凑结构列出实例清单。
2. 每个实例生成局部裁剪图，不能只看整图。
3. 对重复行结构检查首行、中间行、末行。
4. 对连接标签检查是否进入左右模块边框或贴近虚线边界。
5. 对迷你流程检查“文字 -> 图标 -> 箭头 -> 图标 -> 文字”的每一段间距。
6. 修复后刷新 PNG、SVG、PDF、fixed-background drawio，并更新审计记录。

## 放行标准

只有当“报告问题 -> 缺陷类型 -> 全图扫描范围 -> 修复策略 -> 证据文件 -> 残余风险”全部写入审计记录，并且所有同类元素都有局部证据时，才允许把图交付为审稿人视角可用版本。
