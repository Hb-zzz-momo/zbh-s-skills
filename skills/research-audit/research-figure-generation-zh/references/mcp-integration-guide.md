# 科研绘图 MCP 接入与使用教程

## 总原则

科研绘图 MCP 不是一个工具包全包。按证据属性分流：

| 图型 | 首选 MCP | 边界 |
|---|---|---|
| 真实数据图、统计图、多面板结果图 | `local_python_figure` | 只能基于真实表格或结果文件绘图，不编造 P 值、样本量、显著性 |
| 流程图、系统架构图、实验路线图、结构关系图 | `drawio` | 生成可编辑 `.drawio` 或打开 draw.io 编辑器，适合结构图主线 |
| 生物医学机制图、通路图、细胞/分子图标检索 | `biorender` | 需要 BioRender 账号授权；用于图标和模板，不替代事实核对 |
| SVG/PDF 精修、矢量清理、最终导出 | `inkscape` | 用于出版级矢量处理；不要用来篡改数据图数值 |
| WPS 文档/演示插入、最终材料整合 | `wps-office`（若当前会话可用） | 适合把已验收图插入 docx/pptx；不要把 WPS 插入图等同于 draw.io 逐元素编辑 |

## 已接入的 Codex MCP 名称

在 `C:\Users\zbh\.codex\config.toml` 中使用这些 server 名称：

- `drawio`
- `local_python_figure`
- `biorender`
- `inkscape`

可选或延迟暴露的办公整合工具：

- `wps-office`：若当前 Codex 会话或插件环境暴露该工具，用于把已验收图插入 WPS/Office 文档或演示；不作为结构图主编辑器。

在 Codex TUI 中输入 `/mcp` 查看是否已加载。远程服务是否需要登录、能否登录，以当前宿主的 MCP 认证支持为准。

## 1. drawio-mcp：可编辑科研结构图

### 当前接入边界

本机配置的 `drawio` 指向官方 npm 包 `@drawio/mcp`。该 MCP 是用于把 XML、CSV 或 Mermaid 图打开到 draw.io/diagrams.net 编辑器中的工具服务器，不是无头渲染/导出服务器。

当前本地探测到的工具为：

- `open_drawio_xml`
- `open_drawio_csv`
- `open_drawio_mermaid`

注意：

- 新增或修改 `C:\Users\zbh\.codex\config.toml` 后，需要重启 Codex/IDE 会话，当前会话通常不会热加载新的 `mcp__drawio__...` 工具。
- `search_shapes` 属于 draw.io MCP App Server 场景；本地 `@drawio/mcp` 工具服务器不暴露该工具。
- 如果目标是稳定产出 PNG/SVG/PDF，应使用 draw.io Desktop CLI 或 Inkscape MCP 做导出；`@drawio/mcp` 的主要价值是打开可编辑图。
- 截图复现不能只依赖 draw.io MCP 自动完成。应先生成结构化 `.drawio`/mxGraph XML，再在 draw.io 中用真实图标库或 SVG 图标做人工精修，最后导出。
- draw.io MCP 打开成功不等于视觉通过。必须检查真实编辑器画布，尤其是小卡片、表格、连接标签、嵌套流程和图标文本组合。

### 适合

- 实验流程图
- 系统架构图
- 算法 pipeline
- 机制图的结构草稿
- 方法章节总览图

### 不适合

- 真实统计图
- 需要精准图标库的细胞/分子示意图
- 复杂出版级 SVG 最终修边

### 使用方式

提示词模板：

```text
用 drawio MCP 生成一张可编辑的科研结构图。
图型：实验流程图
用途：论文 Methods 主图
核心信息：从样本采集到模型评估的完整流程
必须包含：Sample collection, Preprocessing, Feature extraction, Model training, Evaluation
不得包含：虚构样本量、P 值、显著性、未给出的实验条件
布局：从左到右，5 个主节点，箭头连接
输出：优先 .drawio，可打开编辑；如支持则同时导出 SVG/PDF
```

验收：

- 箭头方向是否符合真实流程
- 节点是否缺失或多出
- 标签是否简洁、无错字
- 是否可继续在 draw.io 中手动编辑

### 结构图复现注意

系统架构图、流程图和论文方法图不能只用代码画矩形和文字占位。若原图含有图标、软件组件符号或领域图形元素，必须至少采用一种真实矢量资产来源：

- Draw.io / diagrams.net 图标库或 `.drawio` 源文件。
- Lucide、Font Awesome、Material Symbols 等可审计 SVG 图标库。
- Inkscape 对现有 SVG 元素做最终对齐、清理和导出。

禁止把 `API`、`USR`、`DB` 这类字母占位符当作图标复现结果交付；最多只能作为低保真草图。

### 可编辑性分级

draw.io 交付必须说明是哪一级：

- **原生可编辑**：模块、文字、箭头、表格和图标尽量由 draw.io 形状组成；必须真实打开检查布局。
- **半可编辑**：文字、模块和箭头可编辑，复杂图标为嵌入 SVG 或组合图形。
- **固定背景**：稳定 SVG/PNG 作为 draw.io 背景，仅适合查看、标注或轻量加字；不能声称逐元素可编辑。

如果原生 `.drawio` 打开后文字挤压、模块错位或图标丢失，应降级为固定背景交付，并明确说明可编辑限制。

## 2. local-python-figure-mcp：真实数据图

### 适合

- line / scatter / bar / box / violin
- heatmap / correlation heatmap
- 从 CSV、TSV、XLSX 生成论文图

### 强制边界

- 不从图片反推数据
- 不推断 P 值、样本量和显著性
- 不生成虚构误差线
- 不执行用户提供的任意 Python 脚本

### 标准流程

先检查表：

```text
用 local_python_figure.inspect_table 检查 D:\project\paper\data\result.csv，
列出列名、类型、缺失值和前 8 行。不要绘图。
```

再绘图：

```text
用 local_python_figure.plot_table 生成论文数据图：
table_path=D:\project\paper\data\result.csv
plot_type=box
x=group
y=score
hue=method
title=Model performance by group
formats=png,svg,pdf
show_points=true
不要添加显著性星号，不要推断 P 值。
```

输出会包含：

```text
figures/<plot-type>-<timestamp>/
  <title>.png
  <title>.svg
  <title>.pdf
  plot_spec.json
  caption.md
```

论文 caption 中必须由用户补充：

- n 或样本来源
- 误差线定义
- 统计检验
- 显著性阈值
- 生物学/技术重复类型

## 3. BioRender MCP：生物医学图标与模板

### 适合

- 细胞结构示意图
- 分子机制图
- 信号通路图
- 生物医学 graphical abstract
- BioRender 图标和模板检索

### 首次授权

BioRender 是远程账号型服务。当前已把官方公开 MCP URL 写入 Codex：

```text
https://mcp.services.biorender.com/mcp
```

在 Codex 中先用 `codex mcp list` 查看状态。若 BioRender 显示 `Auth Unsupported`，说明当前 Codex CLI 只能保存该远程 URL，未暴露 BioRender 文档里的连接器登录流；这种情况下应在支持 Connectors/Integrations 的宿主里完成 BioRender 登录，或等 Codex 侧支持该服务的认证握手。不要把 BioRender API key 写进 prompt、`.env` 或普通配置文件。

### 使用方式

```text
用 biorender MCP 搜索与 mitochondrial apoptosis pathway 相关的图标或模板。
只返回可用于机制图的候选素材，不要编造通路关系。
我的真实节点是：BAX, BCL-2, cytochrome c, caspase-9, caspase-3。
```

### 验收

- 图标是否匹配真实实体
- 通路关系是否来自用户提供内容或文献证据
- 是否把 BioRender 模板误写成实验结果

## 4. Inkscape MCP：最终 SVG/PDF 精修

### 适合

- SVG 元素对齐
- 统一字体、线宽、颜色
- 导出 PNG/PDF/EPS/DXF
- 处理 draw.io、Mermaid、Python 生成的 SVG

### 不适合

- 修改数据图数值
- 手工移动点位来美化统计结论
- 在无事实依据时添加显著性标注

### 使用方式

```text
用 inkscape MCP 打开 figures/model-performance/output.svg。
请只做版式精修：
1. 统一字体为 Arial
2. 线宽统一为 1.2 pt
3. 标签不重叠
4. 导出 output-final.svg 和 output-final.pdf
不得改变坐标轴、数据点、箱线图位置或数值含义。
```

## 5. WPS：文档/演示整合与轻量编辑

WPS 适合把已验收的 SVG/PNG/PDF 放入论文、课程报告、答辩 PPT 或项目文档。它不是 draw.io 源文件的替代品。

### 适合

- 把最终图插入 `.docx` 或 `.pptx`。
- 调整页面位置、大小、标题、图注。
- 在固定背景图上添加少量标注。

### 不适合

- 精准编辑 draw.io 内部 mxGraph 结构。
- 重新排版复杂结构图的所有节点、图标和箭头。
- 对真实数据图做会改变数据含义的手工移动。

### 交付说明

若用户问“能否放到 WPS 编辑”，必须区分：

- 插入 SVG/PNG/PDF 后可在 WPS 中缩放、裁剪和加注释。
- 若要逐元素编辑，需要另做 Office 原生形状版本或在 draw.io 中编辑后重新导出。
- 固定背景版适合稳定展示，不适合拆解成原生表格、箭头和图标。

## 推荐组合链路

### 机制图

```text
brief.md -> drawio 结构草图 -> BioRender 图标素材 -> Inkscape SVG 精修 -> check.md
```

### 真实结果图

```text
数据表 -> local_python_figure.inspect_table -> local_python_figure.plot_table -> Inkscape 只做版式精修 -> caption.md/check.md
```

### 图形摘要

```text
brief.md -> drawio 分层布局 -> BioRender/AI 概念素材 -> Inkscape/Figma 版式 -> check.md
```

### 已有架构图/流程图复现

```text
参考图 -> 元素清单/图标清单 -> drawio 原生结构草图 -> 真实 SVG 图标/图标库 -> Inkscape 稳定 SVG/PDF -> fixed-background drawio/WPS 插入版 -> 全图裁剪审计 -> check.md
```

需要逐元素编辑时，再单独交付 draw.io 原生可编辑版；如果打开后布局不稳定，不能把它作为正式可编辑版本放行。

## 每张图的交付目录

```text
figures/<figure-slug>/
  brief.md
  prompt.md
  source.drawio 或 source.mmd 或 figure.py
  output.png
  output.svg 或 output.pdf
  plot_spec.json（数据图）
  check.md
  caption.md
```

## 最低验收清单

- 科学事实是否来自用户材料、真实数据或明确文献
- 是否存在编造数据、样本量、P 值、显著性
- 箭头方向、节点名、图层关系是否正确
- 标签是否可读、无错字、不重叠
- 图标是否来自真实矢量资产，不能是字母占位符
- SVG/PDF 是否可编辑
- draw.io/WPS 目标软件打开后是否仍然不乱版
- 是否保留源文件、prompt、绘图规格和 caption 草稿
