# PRESENTATION_DESIGN

## Design Read

这是一套“现代主义编辑部 + 投资人路演”的教学视觉：信息层级极端清楚、标题占据页面主导、页面不依赖传统 PPT 标题栏。视觉隐喻是“从模糊想法进入可验证轨道”，通过细箭头、编号、代码裁切和黑/白/蓝背景切换表达反馈节奏。

从参考图延续：

- 黑、白、皇家蓝三类整页底色。
- 超大、全大写或中英混排的无衬线标题。
- 01/02/03 大编号、细箭头、微型页眉和强留白。
- 黑白视觉块或界面裁切，不使用彩色图库照片。
- 页面家族变化明显，但色彩和字体极度统一。

明确避免：复制参考品牌、装饰性渐变、蓝紫 AI 光效、玻璃拟态、圆角卡片墙、图标堆砌、整页项目符号。

## Quantified Direction

| 维度 | 值 | 理由 |
| --- | ---: | --- |
| LAYOUT_VARIANCE | 9 | 12 页覆盖封面、目录、编号问题、流程、代码界面、矩阵和收束 |
| VISUAL_DENSITY | 6 | 教学信息足够，但保留路演级留白 |
| COLOR_INTENSITY | 8 | 皇家蓝承担章节峰值和课堂行动 |
| IMAGE_DOMINANCE | 4 | 以原生代码界面与几何构图替代图库照片 |
| MOTION_INTENSITY | 2 | 静态交付，不依赖动画理解 |

## Canvas and Grid

- 画布：13.333 × 7.5 in，16:9。
- 安全边距：左/右 0.38 in，上 0.32 in，下 0.32 in。
- 栅格：12 列；列间距 0.16 in。
- 基准间距：0.08 / 0.16 / 0.24 / 0.40 / 0.64 in。
- 标题可以贴近左上安全区，不使用居中标题。

## Color Tokens

| Token | Hex | 用途 | 禁止用途 |
| --- | --- | --- | --- |
| BLACK | `050505` | 黑底页面、主要英文标题、代码块 | 不用于大面积正文底色叠加 |
| WHITE | `FFFFFF` | 纯白文字、白底页面 | 不与浅灰直接组合成小字 |
| PAPER | `F5F3EF` | 暖白编辑部页面 | 不做渐变 |
| BLUE | `0B55C8` | 皇家蓝整页底色、编号、关键词 | 不与黑色小字叠加 |
| BLUE_DARK | `073E96` | 蓝字需要更高对比的正文/小标签 | 不替代主蓝整页色 |
| INK | `090A0C` | 白/暖白页正文 | 黑底上禁用 |
| MUTED | `555D66` | 来源、说明、小字 | 小于 9 pt 禁用 |
| SOFT | `D8D5D0` | 分隔线、界面边框 | 不作为正文色 |

## Typography

- 英文标题：Arial / Helvetica Neue / sans-serif，Bold，32–34 pt；封面 42–46 pt。
- 中文标题：Microsoft YaHei / Noto Sans CJK SC，Bold，26–32 pt。
- 正文：Microsoft YaHei，13–16 pt。
- 编号：Arial，Regular，42–54 pt，皇家蓝。
- 微型页眉/来源：Arial + Microsoft YaHei，8–9 pt；正文关键文字不低于 12 pt。
- 标题全部左对齐，行距 0.9–1.0 倍，禁止文字阴影。

## Components

- `microHeader`：页码、章节英文名、课程名；8 pt。
- `sourceFooter`：底部 8 pt，使用来源 ID，不放长 URL。
- `arrowMark`：细线 + 直角/斜向箭头，作为阅读方向提示。
- `codeCrop`：黑白代码/终端界面，1 pt 边框，完全原生文本与形状。
- `proofStamp`：无填充、1.2 pt 线框、轻微旋转，标注“教学示例”“VERIFY”。
- `numberRail`：大号 01/02/03 与小正文错位排列。
- `nativeChart`：仅用于真实/明确标注的示例数据；不使用 3D、渐变或阴影。

## Layout Families

| Family | 页面 | 结构 |
| --- | --- | --- |
| cover-black | S01 | 黑底；左侧超大标题；右侧窄代码裁切 |
| toc-blue | S02 | 蓝底；左上大标题；右下双列目录 |
| unique-white | S03 | 白底；上部大标题与三个原则；下部三段黑白界面 |
| market-blue | S04 | 蓝底；左侧判断；右侧适用/慎用矩阵 |
| problem-numbered | S05 | 白底；01/02/03 沿对角线递进 |
| financials-blue | S06 | 蓝底；五步反馈链；下方三段证据界面 |
| business-white | S07 | 白底；四项提示公式；右侧完整提示样例 |
| screenshots-blue | S08 | 蓝底；三幅黑白界面并列 |
| team-white | S09 | 白底；四个文件对象横排，像团队成员页 |
| table-white | S10 | 白底；左右两列质量门禁 |
| exercise-blue | S11 | 蓝底；任务、交付物、规则三块但不做等宽卡片墙 |
| closing-black | S12 | 黑底；主张居中偏左；右侧人机责任分工 |

## Page Rhythm

黑（开场）→ 蓝（目录）→ 白（定义）→ 蓝（边界）→ 白（问题）→ 蓝（方法）→ 白（提示）→ 蓝（演示）→ 白（上下文）→ 白（质量）→ 蓝（练习）→ 黑（收束）。

## Machine-readable Theme Contract

```presentation-theme
{
  "slide": {"width": 13.333, "height": 7.5, "margin": 0.38},
  "colors": {"ink": "090A0C", "muted": "555D66", "paper": "F5F3EF", "surface": "FFFFFF", "accent": "0B55C8", "accent2": "073E96", "line": "D8D5D0"},
  "fonts": {"head": "Microsoft YaHei", "body": "Microsoft YaHei", "latin": "Arial", "mono": "Consolas"},
  "sizes": {"hero": 44, "title": 30, "body": 14, "small": 8, "metric": 50},
  "radius": 0,
  "gap": 0.16,
  "layout_families": ["cover-black", "toc-blue", "unique-white", "market-blue", "problem-numbered", "financials-blue", "business-white", "screenshots-blue", "team-white", "table-white", "exercise-blue", "closing-black"],
  "motif": "微型页眉 + 细箭头 + 大编号 + 黑白代码裁切",
  "forbidden_patterns": ["渐变", "玻璃拟态", "发光", "蓝紫AI模板", "圆角卡片墙", "整页项目符号", "彩色图库照片"]
}
```

## Font and Render Fallback

- Windows：Microsoft YaHei + Arial + Consolas。
- Linux CI：Noto Sans CJK SC + Liberation Sans + DejaVu Sans Mono。
- 字体替换后必须重新渲染，标题不得因回退换行超过两行。
