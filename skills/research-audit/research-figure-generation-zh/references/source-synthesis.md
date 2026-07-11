# 外部科研生图 Skill 来源提炼

## 全量扫描结论

- 扫描根目录：`外部skill压缩包/research-academic/`
- 扫描对象：全部 `SKILL.md`
- 数量：148 个 skill
- 另有一个科研图 prompt 库：`awesome-research-figure-prompts`

## 核心生图来源

### `gpt-image`

提炼点：

- 先分类为生成、编辑、局部重绘或多参考图。
- 调用前确认资产类型、文字、比例、参考图、安全和预算。
- 先搜参考图库和 craft 规则，再执行生成。
- 论文图、密集标签、中文文本、海报、diagram 使用高质量模式。
- 输出时报告文件路径、关键参数和后续精修建议。

本技能吸收为：科研图 prompt 必须先有 brief，生成后必须报告路径和风险。

### `generate-image`

提炼点：

- 通用图像生成适合照片、插画、概念图、展示背景。
- 技术图、流程图、通路图和系统架构应转给 scientific-schematics。
- 科研文档中可生成癌细胞、DNA、实验室场景、展示背景等概念视觉。
- 支持编辑已有图片。

本技能吸收为：概念视觉可用 AI，技术结构图优先用科研示意图路线。

### `scientific-schematics`

提炼点：

- 面向神经网络架构、系统图、流程图、生物通路、方法流程、技术示意图。
- 使用文档类型质量阈值：journal 高于 poster/presentation。
- 评价维度包括科学准确性、清晰度、标签、布局和专业外观。
- prompt 应包含图型、组件、连接关系、方向、标签和颜色要求。
- 强调色盲友好、可读标签、无重叠、白底或浅底。

本技能吸收为：科研示意图必须先锁节点和关系，并过质量 gate。

### `scientific-visualization`

提炼点：

- 面向期刊级数据图、多面板 figure、误差线、显著性、期刊格式。
- 优先用 Matplotlib/Seaborn/Plotly 生成可复现图。
- 要求色盲友好、灰度可读、正确 DPI/格式、统一字体和面板标号。
- 强调统计严谨：误差线类型、样本量、显著性说明、个体点。

本技能吸收为：真实数据图不得只用 AI 生图，必须保留代码和统计说明。

### `infographics`

提炼点：

- 适合统计信息图、时间线、流程、对比、列表、地图、层级结构。
- 需要事实准确时先研究，再生成。
- 有类型、风格、色盲安全 palette 和质量阈值。
- 质量评价包含层级、排版、数据表达、颜色可访问性、整体影响。

本技能吸收为：综述型科研图和科普图可用 infographic 结构，但事实必须先锁定。

### `scientific-slides`

提炼点：

- 科研展示要视觉优先，避免文字墙。
- 每页需要强视觉元素，并用引用建立研究背景。
- 生成连续幻灯片时要保持统一格式，后续图可附前一张作为风格参考。
- 结果页应优先附已有数据图，不要重新发明结果。

本技能吸收为：汇报图和幻灯片图强调一致风格、引用和已有结果图复用。

### `latex-posters`

提炼点：

- 海报图必须大字、少元素、强留白、远距离可读。
- 每个图只表达一个信息，复杂内容拆图。
- 海报 AI 图常见失败是元素太多、文字太小、内容溢出。
- A0 图形 prompt 应明确 3-4 个元素、10-15 个词、50% 以上留白、巨大字体。

本技能吸收为：海报生图单独设置严格密度限制。

## 可复现图和结构图来源

### `markdown-mermaid-writing`

提炼点：

- 结构关系图应先用 Mermaid 作为文本源图。
- Mermaid 便于 git diff、后续编辑、转图片和 AI 理解。
- 流程、时序、ER、状态、甘特、C4、mindmap、timeline、sankey、xy chart 等应按图型选择。

本技能吸收为：流程/架构/关系图先写文本源图，再决定是否 AI 精修。

### `matplotlib`

提炼点：

- 适合完全控制图形元素、子图、多格式导出。
- 推荐面向对象接口，显式 `fig, ax`。
- 保存时使用 300 DPI、PDF/SVG 矢量格式和 `bbox_inches='tight'`。

本技能吸收为：论文数据图必须保留绘图代码和导出规范。

### `seaborn`

提炼点：

- 适合统计分布、分类比较、回归、热图、分面图。
- 推荐长表数据、语义映射、置信区间和色盲 palette。
- Figure-level 用于快速分面，Axes-level 用于自定义多面板。

本技能吸收为：统计图先考虑 seaborn，发表前再按 scientific-visualization 收口。

### `networkx`

提炼点：

- 适合复杂网络、知识图谱、生物网络、交通/引用网络。
- 可用节点大小表示中心性、颜色表示社区、边宽表示权重。
- 网络图需要固定随机种子，保存 PDF/SVG/PNG。

本技能吸收为：网络类科研图必须从真实边表/节点表构建，不用纯 AI 编造拓扑。

## prompt 库来源

`awesome-research-figure-prompts` 提供 9 类科研图：

| 类别 | 用途 |
|---|---|
| mechanisms-pathways | 分子机制、信号通路、调控网络 |
| process-workflow | 实验流程、测序流程、计算流程、方法管线 |
| graphical-abstracts | 论文图形摘要和核心机制总览 |
| lab-apparatus | 实验装置、仪器配置、实验系统 |
| micro-structures | 微观结构、材料结构、细胞/组织细节 |
| systems-networks | 模型架构、系统拓扑、蛋白互作、代谢网络 |
| journal-covers | 期刊封面、传播视觉、强表现力科学图 |
| cross-sections-layers | 剖面、层级结构、器官/材料/地质层 |
| environments-ecologies | 环境生态、循环、食物网、地理生态系统 |

常见视觉风格：

- `Schematic Minimal`：低噪声、适合论文主图和方法图
- `Clean Vector`：清晰矢量边界，适合图形摘要和系统图
- `Isometric Technical`：适合架构、设备、工程系统
- `Scientific Engraving Monochrome`：适合黑白期刊风格
- `Watercolor Texture & Ink Line Atlas`：适合生物、生态、图鉴类
- `3D Cutaway`：适合剖面和层级结构
- `Journal Cover Cinematic`：适合封面和传播图，不适合严肃数据图

## 领域型 skill 的处理

全量扫描还发现大量领域技能包含可视化片段，例如 `scanpy`、`scvelo`、`scvi-tools`、`bulk-rnaseq`、`deeptools`、`histolab`、`pydicom`、`imaging-data-commons`、`geopandas`、`phylogenetics`、`rdkit`、`pymatgen`、`timesfm-forecasting`、`shap`、`umap-learn` 等。

这些不应被合并成 AI 生图 prompt，而应作为“数据语义来源”：

- 单细胞图：保留真实 embedding、cluster、marker、trajectory。
- 医学影像图：保留真实 DICOM/病理图来源和匿名化要求。
- 地理图：保留投影、坐标、比例尺和图例。
- 分子/材料图：保留结构式、晶体结构、轨道/相图的真实计算来源。
- 时间序列/预测图：保留区间、异常点和预测元数据。

本技能只负责把这些领域图统一到科研生图和发表验收流程中，不替代领域数据分析。
