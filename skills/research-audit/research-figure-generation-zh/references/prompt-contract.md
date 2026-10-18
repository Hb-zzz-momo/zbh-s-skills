# 科研生图 Prompt 契约

## 基础模板

```text
Create a [figure type] for [research context].

Core message:
[one sentence claim]

Must include:
- [entity/component 1]
- [entity/component 2]
- [relationship/arrow/flow]

Layout:
[left-to-right / top-to-bottom / circular / multi-panel / layered cross-section]

Labels:
Use exactly these labels: [label list].
Do not add extra labels or invented values.

Scientific constraints:
- Preserve [known relationship/fact].
- Do not invent sample sizes, p-values, concentrations, dates, or unprovided statistics.
- Keep arrows and causal directions scientifically correct.

Visual style:
[Schematic Minimal / Clean Vector / Isometric Technical / Scientific Engraving Monochrome / 3D Cutaway / Journal Cover Cinematic]

Accessibility and publication quality:
White or light background, high contrast, colorblind-safe palette, readable sans-serif labels, no overlapping text, balanced spacing, clean margins.

Output:
[aspect ratio / target use / resolution / transparent or opaque background]
```

## 中文填写模板

```text
请生成一张用于[论文/汇报/海报/基金/封面]的[图型]。

核心信息：
[一句话说明这张图要表达什么]

必须包含：
- [对象/变量/节点/步骤]
- [对象/变量/节点/步骤]
- [箭头关系/层级关系/对比关系]

布局：
[从左到右/从上到下/中心辐射/分层剖面/多面板]

标签：
只使用这些标签：[标签清单]。
不要自行添加未经提供的数值、P 值、样本量、分子名或实验条件。

科学约束：
- [必须保持的因果方向或机制关系]
- [必须避免的错误]

视觉风格：
[简洁科研示意图/干净矢量/等距技术图/黑白线稿/三维剖面/期刊封面视觉]

发表质量：
白底或浅底，高对比度，色盲友好，标签清晰，无文字重叠，留白充足，适合[目标场景]阅读。
```

## 类型模板

### 已有图片复现 / image2 结果复现

复现已有图时，prompt 或执行 brief 必须先写清楚：

```text
Reference figure reproduction task.

Visual target:
- Match the reference layout, hierarchy, labels, color grouping, arrow directions, icon semantics, and output aspect ratio.

Editability target:
- Delivery level: [L0 visual stable / L1 fixed-background editable wrapper / L2 partially editable / L3 fully native editable].
- Do not claim full editability if the final file is a fixed background image.

Element inventory:
- Panels:
- Required labels:
- Icons and symbol types:
- Tables or repeated rows:
- Connectors and arrow labels:
- Legend/caption/footer:

Asset constraints:
- Use real vector icons or hand-built SVG icons for browser, user, database, API, GitHub, chart, table, medical or mechanism symbols.
- Do not use letter placeholders such as API, DB, USR as final icons.
- Mark uncertain OCR or unreadable text as "needs confirmation" instead of inventing text.

Quality gates:
- No text overflow, no label-border collision, no icon-text collision, no table row overflow.
- Open and inspect the target editor when delivering draw.io or WPS files.
- Produce local crops or contact sheet for compact panels and repeated table/card structures.
```

中文模板：

```text
请复现这张参考图，目标不是重新设计，而是在保持结构、层级、标签、箭头方向和图标语义的前提下，生成可审稿的科研图。

视觉目标：
[像素级接近/结构接近/风格接近/内容等价]

编辑目标：
[L0 视觉稳定版 / L1 固定背景可打开版 / L2 半可编辑版 / L3 全原生可编辑版]

必须复现：
- 主面板：
- 标签：
- 图标：
- 表格/重复行：
- 箭头和连接标签：
- 图例/底部区域：

禁止：
- 不使用 API、DB、USR 等字母占位符冒充图标。
- 不把 fixed-background drawio/WPS 文件说成完全可编辑。
- 不自行发明看不清的 OCR 文本。
- 不在目标软件未打开验收前声称可编辑交付完成。
```

### 机制通路图

重点字段：

- 细胞空间：membrane、cytoplasm、nucleus、mitochondria
- 节点类型：receptor、ligand、kinase、transcription factor、gene
- 边类型：activation、inhibition、phosphorylation、translocation、feedback
- 审核重点：箭头方向、抑制符号、核转位、负反馈

### 实验流程图

重点字段：

- 输入样本
- 实验步骤
- 关键仪器或试剂
- 输出数据
- 后续分析

用语建议：

```text
Show as a clean left-to-right workflow with 5 steps maximum. Each step has one icon, one short label, and one output. Avoid dense protocol text.
```

### 数据图美化

AI 编辑已有数据图时必须写：

```text
Preserve all data geometry exactly. Do not change point positions, bar heights, curve shapes, error bars, p-values, axis values, or labels. Only improve typography, spacing, panel alignment, color palette, legend placement, and visual clarity.
```

### 图形摘要

结构建议：

```text
Three-zone graphical abstract:
Left: problem/background.
Center: proposed method or mechanism.
Right: key outcome or implication.
Use arrows to show progression. Keep fewer than 8 labels total.
```

### 海报图

硬约束：

```text
POSTER FORMAT. Maximum 3-4 elements. Maximum 10-15 words total. Very large bold labels. 50% white space. Readable from 6-10 feet. No small captions. No nested details.
```

## 负面约束库

按需添加：

- no invented data
- no fake p-values
- no unreadable small text
- no decorative clutter
- no overlapping labels
- no extra abbreviations
- no stock-photo style
- no glossy marketing look for manuscript figures
- no 3D effects for quantitative charts
- no red-green-only encoding
- no misleading causal arrows

## prompt 改写流程

1. 把用户原话拆成“图型、事实、关系、风格、输出规格”。
2. 删除泛泛形容词，例如 advanced、beautiful、high-tech，改成可验收描述。
3. 对缺失事实标注“待确认”，不要自行补。
4. 加入负面约束和发表质量要求。
5. 若是复现已有图，先写元素清单和交付等级，再生成 prompt 或代码。
6. 生成后根据验收问题定向改 prompt，不要盲目重试。
