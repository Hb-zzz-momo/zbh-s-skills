# PRESENTATION_DESIGN

## Design Read

- 场景：工程团队负责人评审一项正式汇报发布门禁。
- 情绪：克制、严谨、可执行；像一篇有明确社论立场的技术专刊，而非营销路演。
- 核心隐喻：三页不是样张，而是三种风险的“校样”。
- 唯一视觉母题：**朱红校样章 + 深绿页码轨道**。朱红只标记需要判断、阻断或行动的元素；深绿承担结构、流程和主标题。
- 应延续：暖白纸张质感、编辑部式不对称网格、细线分栏、页码与短标签、留白形成的节奏。
- 应避免：紫蓝渐变、发光边框、同尺寸三列卡片、每页相同标题横线、无意义图标、整页截图。

## Quantified Direction

- LAYOUT_VARIANCE: 8/10 — 六页使用 hero、纵栏、流程、数据、清单、行动六种构图，但共享同一网格和母题。
- VISUAL_DENSITY: 6/10 — 技术汇报需要信息完整，但每页只保留一个结论焦点。
- COLOR_INTENSITY: 5/10 — 暖白为主，深绿占大面积，朱红只做约 8–12% 的判断性强调。
- IMAGE_DOMINANCE: 1/10 — 不使用外部图片，以原生形状、线条、图表和文字为主。
- MOTION_INTENSITY: 0/10 — 不依赖动画，所有关系在静态渲染中成立。

## Canvas and Grid

- 比例：16:9
- 尺寸：13.333 × 7.5 in
- 安全边距：左右 0.62 in；上 0.52 in；下 0.42 in
- 基准间距：0.16 in；常用倍数 0.32 / 0.48 / 0.64 in
- 栅格：12 列；列间距 0.16 in；内容区 12.09 in
- 顶部标题区：0.52–1.42 in；主体区：1.52–6.82 in；来源区：6.98–7.16 in
- 最小对象间距：0.12 in；文字与容器内边距至少 0.14 in

## Color Tokens

| Token | Hex | 用途 | 禁止用途 |
|---|---|---|---|
| `PAPER` | `F4EFE5` | 全页背景、暖白纸张 | 不用于正文文字 |
| `PAPER_2` | `FBF8F1` | 浅色内容块、数据绘图区 | 不与 PAPER 形成弱对比小字 |
| `FOREST` | `193C34` | 标题、主结构、流程、深色面板 | 不与朱红等量竞争 |
| `FOREST_2` | `2E5B4D` | 次级结构、图表主系列 | 不用于低字号来源 |
| `VERMILION` | `A93624` | Gate、问题、行动、校样章 | 不作为大面积背景超过页面 15% |
| `INK` | `1E2925` | 正文、数据标签 | 不在 FOREST 上使用 |
| `MUTED` | `56625C` | 注释、次级说明 | 不用于小于 11 pt 的正文 |
| `LINE` | `D7CDBE` | 分隔线、浅描边、网格 | 不承担主信息关系 |
| `WHITE` | `FFFFFF` | 深色面板上的文字 | 不作为整页背景 |

## Typography Tokens

| Token | 字体回退链 | 字号 | 字重 | 行距 |
|---|---|---:|---:|---:|
| `HERO` | Microsoft YaHei, DengXian, sans-serif | 38–42 pt | Bold | 1.05 |
| `TITLE` | Microsoft YaHei, DengXian, sans-serif | 27–31 pt | Bold | 1.08 |
| `SUBTITLE` | Microsoft YaHei, DengXian, sans-serif | 17–19 pt | Regular | 1.25 |
| `BODY` | Microsoft YaHei, DengXian, sans-serif | 15–17 pt | Regular | 1.28 |
| `BODY_STRONG` | Microsoft YaHei, DengXian, sans-serif | 16–18 pt | Bold | 1.18 |
| `LABEL` | Microsoft YaHei, DengXian, sans-serif | 10.5–12 pt | Bold | 1.0 |
| `NOTE` | Microsoft YaHei, DengXian, sans-serif | 9–10.5 pt | Regular | 1.15 |
| `METRIC` | Aptos Display, Microsoft YaHei, sans-serif | 29–34 pt | Bold | 1.0 |

## Components

- 标题：左对齐；结论句优先；上方可有 10.5 pt 朱红 eyebrow；禁止每页同款装饰横线。
- 来源：左下或右下，9 pt MUTED；示例数据页用 9.5 pt VERMILION 加粗标签。
- 数据标注：数值直接标在条形末端；纵轴必须从零开始；单位写在图表标题或轴旁。
- 图片框：本任务不使用外部图片。
- 图标：只允许由原生几何构成的语义符号；不得用图标替代文字。
- 图表：原生矩形条 + 数据标签；主系列 FOREST_2，对照系列 VERMILION；绘图区 PAPER_2。
- 校样章：细朱红描边、轻微旋转（±2°）、全大写英文或 4–8 字中文；仅用于 Gate/示例/批准。
- 页码轨道：左侧 0.12 in 深绿短轨道 + `01/06` 编号；封面用三张纸替代页码轨道。

## Layout Families

| Family | 适用页面 | 结构 | 约束 |
|---|---|---|---|
| `hero-editorial` | S01 | 左 7 列大标题，右 5 列三页叠纸 | 右侧视觉必须传递“三页”而非装饰 |
| `risk-probes` | S02 | 三个不同高度的纵向校样栏 | 禁止等高卡片；问题句为主，编号与风险次之 |
| `gated-process` | S03 | 5 步横向链路 + 右侧 Gate 分支 | 箭头单向，FAIL 回路不穿文字 |
| `data-focus` | S04 | 左 7 列图表，右 5 列解释与限制 | 示例标签在标题上方；数据焦点唯一 |
| `dod-checklist` | S05 | 左右不等宽清单 + 底部 BLOCK 条 | 不使用勾选图标墙；用编号与细线组织 |
| `decision-action` | S06 | 大请求 + 三项承诺 + 决策规则 | 朱红只落在“批准”与 Gate 规则 |

## Rhythm and Motif

- 开场：大留白 + 右侧三张校样纸，信息密度低。
- 内容段：S02 纵向分栏，S03 横向链路，方向与密度逐步上升。
- 高密度页：S04 用单一图表释放认知负担；S05 以条目节奏收束执行细节。
- 收束：S06 回到大留白和单一行动，朱红校样章完成首尾呼应。
- 母题变化：三张纸 → 三个风险栏 → Gate 章 → 示例章 → BLOCK 条 → 批准章；重复语义，不重复构图。

## Forbidden Patterns

- 连续三页同尺寸卡片网格。
- 大面积朱红背景或深绿/朱红等权竞争。
- 字号低于 9 pt；正文低于 14 pt。
- 线条穿越文字、箭头无方向、对齐依靠空格。
- 用示例数字暗示真实 ROI。
- 页面装饰多于信息对象。

## Font and Render Fallback

- 首选 Microsoft YaHei；若缺失则 DengXian；英数指标可用 Aptos Display，缺失则回退 Microsoft YaHei。
- 构建前检查字体；真实 PowerPoint/WPS 渲染后检查替换、行高、换行与数字基线。
- 所有文本框保留 0.04–0.08 in 内边距，并优先固定字号而非自动缩放。

## Machine-readable Theme Contract

```presentation-theme
{
  "slide": {"width": 13.333, "height": 7.5, "margin_x": 0.62, "margin_top": 0.52, "margin_bottom": 0.42},
  "grid": {"columns": 12, "gutter": 0.16, "base_gap": 0.16},
  "colors": {"paper": "F4EFE5", "paper2": "FBF8F1", "forest": "193C34", "forest2": "2E5B4D", "vermilion": "A93624", "ink": "1E2925", "muted": "56625C", "line": "D7CDBE", "white": "FFFFFF"},
  "fonts": {"head": "Microsoft YaHei", "body": "Microsoft YaHei", "fallback": "DengXian", "metric": "Aptos Display"},
  "sizes": {"hero": 40, "title": 29, "subtitle": 18, "body": 16, "label": 11, "note": 9.5, "metric": 32},
  "stroke": {"hairline": 0.8, "regular": 1.3, "gate": 2.0},
  "radius": 0.04,
  "gap": 0.32,
  "layout_families": ["hero-editorial", "risk-probes", "gated-process", "data-focus", "dod-checklist", "decision-action"],
  "motif": "朱红校样章与深绿页码轨道",
  "forbidden_patterns": ["连续三页同尺寸卡片", "默认紫蓝渐变", "无意义发光", "装饰横线复用", "示例数据冒充真实数据"]
}
```
