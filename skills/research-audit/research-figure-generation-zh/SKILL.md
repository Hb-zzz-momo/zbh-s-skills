---
name: research-figure-generation-zh
description: '科研生图与论文配图总控技能：用于设计、生成、复现、改造和验收科研论文图、图形摘要、机制通路图、实验流程图、系统架构图、数据可视化、多面板 figure、海报/幻灯片视觉图、期刊封面风格图，以及 draw.io/WPS 可编辑图和 MCP 科研绘图交付。Use when: 科研生图、论文配图、scientific figure、graphical abstract、schematic、机制图、通路图、实验流程图、系统架构图、已有图片复现、image2 图复现、draw.io、WPS、科研绘图 MCP、数据图、结果图、美化图表、AI 生成科研图、科研海报图、论文插图、期刊级 figure 验收。'
---

# 科研生图与论文配图总控

## 目标

把科研图从“随便生成一张好看的图”提升为可复现、可审稿、可修改的图形生产流程。优先保证科学事实、图意结构和发表规范，其次才追求视觉风格。

## 来源综合

本技能由 `外部skill压缩包/research-academic/` 全量扫描后合成，扫描到 148 个 `SKILL.md`，重点吸收以下来源：

- AI 生图执行：`gpt-image`、`generate-image`
- 科研示意图：`scientific-schematics`
- 期刊数据图：`scientific-visualization`、`matplotlib`、`seaborn`
- 信息图与展示图：`infographics`、`scientific-slides`、`latex-posters`
- 结构化源图：`markdown-mermaid-writing`、`networkx`
- prompt 素材库：`awesome-research-figure-prompts` 的 9 类科研图 prompt

需要查看完整来源提炼时，读取 `references/source-synthesis.md`。

## 工作流

### Step 1: 图型分流

先判断用户要的是哪类图，不要直接生图：

| 需求 | 默认路线 |
|---|---|
| 数据结果图、统计图、多面板结果图 | Python 绘图优先，见 `scientific-visualization` 思路 |
| 流程、架构、关系、决策链 | Mermaid/矢量源图优先，再转 AI 精修 |
| 机制通路、实验流程、系统示意图 | 先写结构 brief，再用 AI schematic |
| 图形摘要、综述图、概念图 | 先锁主结论和图层，再写完整 prompt |
| 海报/幻灯片大图 | 控制元素数量、字体和留白 |
| 期刊封面/宣传视觉 | 允许更强视觉表现，但不得冒充结果数据 |

详细路由见 `references/figure-types-and-routing.md`。

MCP 接入与使用教程见 `references/mcp-integration-guide.md`。当前推荐链路：

- `drawio`：可编辑科研结构图、流程图、系统架构图。
- `local_python_figure`：真实数据图，基于 CSV/TSV/XLSX 生成 PNG/SVG/PDF。
- `biorender`：生物医学图标、模板和机制图素材检索。
- `inkscape`：SVG/PDF 最终矢量精修和导出。
- `wps-office`：把已验收图插入 Word/PPT、做轻量标注和最终材料整合；不替代 draw.io 原生结构编辑。

局部视觉缺陷的处理协议见 `references/defect-generalization-protocol.md`。正式图中任一局部缺陷都必须先升级为缺陷类型，再对全图同类元素做扫描、修复和证据留存。

已有图片、image2 结果、截图或论文图复现流程见 `references/image-reproduction-workflow.md`。复现类任务必须同时声明“视觉稳定交付”和“可编辑交付”的边界，不能把固定背景文件说成完全可编辑源图。

### Step 2: 锁定科学事实

生成前必须先确认：

- 图要表达的 1 个核心结论
- 必须出现的实体、变量、节点、方法或实验步骤
- 哪些内容来自真实数据，哪些只是概念表达
- 禁止编造的数据、数值、蛋白名、通路关系、显著性、样本量
- 目标用途：论文、汇报、海报、基金、封面、社媒或内部草图

如果事实不完整，先产出“待确认 brief”，不要假装已经知道。

### Step 3: 选择生成策略

按风险从低到高选择：

1. **文本源图**：Mermaid、Graphviz、TikZ，适合流程、架构、关系图。
2. **代码绘图**：Matplotlib、Seaborn、NetworkX，适合真实数据图和可复现实验结果。
3. **MCP/矢量结构图**：draw.io、Inkscape、WPS、BioRender、真实 SVG 图标库，适合结构图复现、系统架构图、机制图精修和可编辑交付。
4. **AI 示意图**：适合机制图、图形摘要、概念图、封面视觉。
5. **AI 编辑**：在已有草图、真实图表、论文图基础上改版、统一风格或增强可读性。

真实数据图不允许只用 AI 生图替代。AI 可以做版式、注释、统一风格，但数值和统计图形必须来自代码或用户给定图。

已有图片复现时必须先选交付等级：

- **视觉稳定版**：优先保证 PNG/SVG/PDF 在目标尺寸下不乱、不溢出，适合论文、汇报和 WPS 插入。
- **固定背景可打开版**：把稳定 SVG/PNG 作为 draw.io/WPS 背景，适合标注和轻量编辑，但不是逐元素可编辑。
- **逐元素可编辑版**：用 draw.io/WPS 原生形状重建模块、箭头、文字和图标，必须在目标软件真实打开后验收；如果打开后布局乱，不能交付为可编辑完成版。

代码只画矩形和文字不能视为高质量复现。若原图包含图标、数据库、浏览器、用户、API、GitHub、表格等符号，必须使用真实矢量图标库、draw.io 图标库、BioRender 素材或手工 SVG 图标，不能用字母占位符冒充。

### Step 4: 写科研图 brief

正式生成前写一个短 brief：

```markdown
图型：
用途：
核心信息：
必须包含：
不得包含：
布局：
风格：
文字标签：
数据/事实来源：
输出规格：
验收标准：
```

如果用户已经给出完整要求，可以直接把 brief 融入 prompt。

### Step 5: 生成 prompt 或代码

使用 `references/prompt-contract.md` 的模板。prompt 必须包含：

- 图型和学科场景
- 主体对象与层级关系
- 布局方向和读图顺序
- 标签清单和禁止标签
- 视觉风格，不超过 2 个主风格词
- 科学准确性约束
- 字体、留白、对比度、色盲友好要求
- 输出尺寸和用途
- 负面约束：不要伪数据、不要多余文字、不要装饰性噪声

### Step 6: 验收与迭代

每张科研图至少过一次验收：

- 科学事实是否对
- 图意是否一眼能读懂
- 标签是否可读且无错别字
- 是否存在重叠、截断、错箭头、假数据
- 色彩是否色盲友好，灰度下是否还能理解
- 期刊/海报/幻灯片尺寸是否匹配
- 是否保存了 prompt、源图或绘图代码

完整验收表见 `references/quality-gates.md`。

正式图不能只按用户指出的局部问题修补。进入最终交付前必须做一次全图审稿式巡检：

- 按标题区、每个主面板、模块间连接区、底部能力区、图例区分别截图或裁剪检查。
- 每个主面板内部若还有嵌套子流程、迷你流程盒、表格组、卡片组，也必须单独裁剪检查。
- 逐块确认文字没有溢出、贴边、嵌入边框、被箭头压住或与图标/表格重叠。
- 对 API 表、数据库表、指标表、能力卡片等重复结构，必须检查首行、中间行和末行。
- `dom_validate`、XML 可解析、MCP 导出成功只能证明文件有效，不能替代视觉放行。
- 若用户指出任一局部问题，修复后必须重新做全图巡检，而不是只复查该局部。

缺陷修复不能停留在“改用户截图里的位置”。一旦用户或自检指出任一问题，必须执行 `references/defect-generalization-protocol.md`：

- 先把局部症状归类为文字溢出、图标/文字碰撞、表格行溢出、连接标签贴边、嵌套小流程拥挤、目标软件渲染错位等缺陷类型。
- 枚举全图所有同类元素，并记录哪些元素被扫描。
- 优先修改统一布局规则、helper 函数、尺寸常量或导出链路，而不是只改单个坐标。
- 为该缺陷类型补充或复用自动审计脚本、局部裁剪图、contact sheet 或目标软件截图证据。
- 更新最终 PNG/SVG/PDF/draw.io/WPS 等下游产物，并在 `check.md` 或审计记录中写明“局部问题 -> 缺陷类型 -> 全局扫描 -> 证据”。

## 输出规范

建议每张图一个文件夹：

```text
figures/<figure-slug>/
  brief.md
  prompt.md
  source.mmd 或 figure.py 或 source.drawio
  assets/
    icons/ 或 references/
  output.png
  output.svg 或 output.pdf（如有）
  output.fixed-background.drawio（如需稳定打开）
  audits/
    crops/ 或 contact-sheet.png
    geometry-audit.json（如有）
  check.md
  caption.md
```

如果只是帮用户写 prompt，可以只输出 brief 和 prompt。若实际生成图片，最终回复必须给出图片路径、使用的 prompt/代码路径和未解决风险。

正式交付必须给出交付状态：

- **PASS**：事实、布局、视觉、目标软件打开效果和导出文件均已验收，残余风险不影响使用。
- **CAUTION**：主要用途可用，但存在明确限制，例如 draw.io 固定背景不可逐元素编辑、BioRender 未授权、WPS 只能插入而不能编辑内部结构。
- **BLOCK**：存在文字重叠、溢出、目标软件打开错位、真实数据不可追溯或关键事实未确认，不能交付为正式图。

## 强制边界

- 不编造数据、样本量、P 值、显著性、实验条件或文献结论。
- 不把 AI 生成的概念图说成实验结果图。
- 不在没有用户授权的情况下写入 API key、`.env` 或上传图像。
- 不把复杂科研图一次性塞满。复杂图先拆成 panels 或多张图。
- 对论文投稿图，优先保存可编辑源文件或可复现代码。
- 不把“MCP 调用成功、XML 可解析、WPS/draw.io 能打开”当成视觉质量通过。
- 不把固定背景 draw.io/WPS 文件说成完全可编辑源文件。

## 常用调用方式

- “用 `$research-figure-generation-zh` 给我的论文方法部分做一张机制图。”
- “把这张结果图改成 Nature 风格多面板 figure。”
- “根据我的研究内容写一个图形摘要 prompt。”
- “帮我生成科研海报的 3 张核心视觉图，每张都要能远距离看清。”
