# Reference Brief：数据科学课程答辩 PPT

## 当前任务

- 交付物：数据科学课程答辩 PPT 的重新设计方案。
- 受众：课程教师与同学。
- 目标：专业科技感、可讲解、数据表达可信。
- 参考维度：科研叙事、跨页节奏、技术层级、图表选型。

## 具体参考

1. [Data Analytics Pitch Deck Design | PowerPoint](https://www.behance.net/gallery/241296893/Data-Analytics-Pitch-Deck-Design-PowerPoint)：观察多页网格、大号结论标题、指标分层与深浅页面节奏。采用层级和节奏；不采用投资人语气、3D 装饰和霓虹配色。
2. [Edutech Presentation Slide](https://www.behance.net/gallery/244120561/Edutech-Presentation-Slide)：观察标题→类别→子类别的树状技术层级和关系连接线。采用真实关系表达；不把单页案例当作整套叙事。
3. [Data Science presentation for future graduate career](https://www.slideshare.net/slideshow/data-science-presentation-for-future-graduate-career-6be5/275964233)：检查 5 页教育叙事，采用“角色/问题→组成→能力→行动”的递进逻辑；排除文字密集与弱层级。
4. [Evolution of the bitcoin price](https://www.data-to-viz.com/story/TwoNumOrdered.html)：采用“按数据关系先选图”的规则；时间序列优先折线图，坐标轴截断必须解释，静态答辩页不滥用探索性交互。

## 可执行规律

1. 故事线使用“背景问题→数据→方法→结果→反思与下一步”。
2. 每页只保留一个结论先行标题。
3. 方法页连接线只表达真实数据流或方法关系。
4. 数据页明确单位、坐标轴、样本或时间范围，先选对图再美化。
5. 可以使用深浅页面节奏，但必须继承当前课程/项目品牌色并限制强调色。

## 下游落实

| 规律 | 落实位置 |
|---|---|
| 单主线叙事 | `storyline.md` / 目录 |
| 结论先行 | `slide-spec.json` 每页 claim |
| 真实流程关系 | 方法流程页 |
| 图表口径 | 实验趋势与模型比较页 |
| 深浅节奏与克制强调色 | `PRESENTATION_DESIGN.md` |

## 明确不采用

- 商业融资 Deck 的市场、财务和团队话术。
- 与课程内容无关的 3D 装饰、霓虹渐变和玻璃卡片。
- SlideShare 案例中的密集项目符号。
- 没有数据关系依据的雷达图或装饰性图表。

## 限制与许可

- Deck.gallery 未返回可核查具体案例，未列为正式参考。
- Behance 公开预览只作观察，不复用模板、字体、插画或品牌资产。
- 本测试只生成 Reference Brief，尚未进入实际 PPT 设计阶段。
