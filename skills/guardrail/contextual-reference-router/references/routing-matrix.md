# 任务路由矩阵

## 使用顺序

1. 先判断交付物与主要问题。
2. 从下表选择 2–5 个来源，至少覆盖两个互补维度。
3. 再到 [source-registry.md](source-registry.md) 检查限制、关键词和许可注意项。
4. 打开具体案例，不能把下表的网站名直接当作参考证据。

| 任务类型 | 首选来源组合 | 主要维度 | 不应作为主来源 |
|---|---|---|---|
| Web 整体视觉 | Awwwards + Land-book + SiteInspire/Recent.design + Coolors + Typewolf | 视觉、首页结构、色彩、字体 | PPT 网站、仅流程网站 |
| Landing Page 页面结构 | Land-book + Lapa Ninja + Awwwards | 首屏、内容节奏、CTA、社会证明、定价 | 单页视觉截图作为唯一证据 |
| Web App / 后台 | Mobbin + Refero + Page Flows | 真实产品结构、组件、状态、流程 | Awwwards 高强度动效 |
| Web 用户流程 | Page Flows + Mobbin + Refero | 步骤、反馈、异常、空状态 | 只看静态 Landing Page |
| Dashboard | Mobbin + From Data to Viz + Apache ECharts Examples + Observable | 产品 UI、图表选型、实现、交互 | 只搜“漂亮 Dashboard” |
| PPT 整体结构 | Deck.gallery + SlideShare + Pitch | 故事线、目录、节奏、真实内容 | Dribbble 单页作为唯一来源 |
| PPT 高端视觉 | Behance + Deck.gallery + Dribbble | 视觉系统、连续性、封面与数据页 | 只看封面 |
| 科研汇报 PPT | Behance + Deck.gallery + SlideShare + From Data to Viz | 科研叙事、视觉、演讲结构、数据图 | 纯商业模板直接套用 |
| Coding Prompt | OpenAI 官方文档 + 对应产品官方文档 + 官方 Cookbook + Cursor Directory/Fabric | 指令层级、工具、约束、验收、失败处理 | Web 视觉网站、低质量聚合 Prompt |
| Cursor Rules / AGENTS.md / CLAUDE.md | 对应产品官方文档 + Cursor Directory + 高质量开源仓库 | 项目规则、上下文、工具与边界 | 社区内容未经官方交叉验证 |
| 数据可视化 | From Data to Viz → Data Viz Project → ECharts → Observable/D3 → Flourish/Datawrapper | 先选图，再实现与叙事 | 先看配色后决定图型 |
| 科研机制图 | BioRender + Behance 科研图案例 + 相关论文真实机制图 | 科学关系、层级、箭头、图例 | SaaS/Landing Page 风格机械套用 |
| 系统架构图 | AWS + Azure + Google Cloud Architecture Centers + Excalidraw Libraries | 边界、服务、数据流、部署、图标 | 无事实依据的装饰性架构图 |
| 配色设计 | 当前行业案例 + Coolors + 对比度检查 | 品牌适配、语义色、可访问性 | 脱离行业的个人偏好 |
| 字体设计 | Typewolf + 当前参考案例排版 + 部署环境可用字体 | 字体组合、层级、实际可用性 | 许可不明或环境不存在的字体 |
| 报告 / 汇报模板 | Behance + SlideShare + Pitch | 报告叙事、章节结构、数据页、字体层级、可编辑模板 | Web 视觉站或单页截图作为唯一证据 |
| 图标与插画系统 | Iconify + unDraw + Behance | 图标语义、插画风格、空状态、品牌适配、素材许可 | 许可不明的素材或为填空加入无关插画 |

## 组合规则

- 结构来源 + 视觉来源 + 专项来源是默认组合，不为凑数增加同质来源。
- 真实产品流程优先于视觉概念稿；科学准确性优先于装饰；官方技术资料优先于社区聚合。
- 若用户提供完整参考图并要求严格局部修改，不额外探索风格；只在用户要求或现有参考缺失时启用本路由。
- 新来源无法增加新的设计维度时停止检索。
