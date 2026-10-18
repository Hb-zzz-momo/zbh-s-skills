# 网站参考源注册表

## 目录

1. PPT 与演示
2. Web/UI 与产品交互
3. Coding Prompt 与 Agent 指令
4. 数据可视化与 Dashboard
5. 科研机制图与系统架构
6. 配色、字体、图标和插画

“具体案例”列为“必须”时，应打开项目页、案例页、多页 Deck、官方示例或论文图，而非仅访问首页。

## 1. PPT 与演示

| 来源 | 域名 | 主要用途 | 适用任务 | 优点 | 局限 | 推荐关键词 | 具体案例 | 注意事项 |
|---|---|---|---|---|---|---|---|---|
| Deck.gallery | `deck.gallery` | 完整 Deck 的页面顺序、密度与节奏参考 | 商业 Deck、产品发布、融资路演、品牌手册、PPT 整体叙事 | 完整页面顺序、密度与节奏 | 行业覆盖不均 | `data science deck`, `product launch`, `investor deck` | 必须 | 检查多页、数据页、封面与结尾 |
| Behance | `behance.net` | 高端 Presentation 与品牌视觉系统参考 | 科技风 PPT、课程答辩、科研汇报、品牌演示 | 完整视觉系统与连续性 | 展示稿可能弱化真实内容 | `technology presentation`, `research presentation` | 必须 | 不复制品牌资产与专有视觉 |
| SlideShare | `slideshare.net` | 真实内容、论证、目录与演讲结构参考 | 商业汇报、教育演示、课程展示 | 真实内容和故事线丰富 | 视觉质量不稳定 | `data science presentation`, `education deck` | 必须 | 不作为高端视觉唯一来源 |
| Pitch | `pitch.com` | 可编辑商业结构与模板参考 | SaaS Deck、产品介绍、市场汇报、项目计划 | 可编辑商业结构 | 模板感可能强 | `SaaS deck`, `product plan template` | 建议 | 检查模板授权与适配 |
| Dribbble | `dribbble.com` | 封面、数据页与单页视觉参考 | PPT 封面、指标页、局部版式探索 | 局部视觉灵感强 | 多为单页，缺完整叙事 | `presentation cover`, `data slide` | 必须 | 不作为整套叙事唯一来源 |
| Slidesgo | `slidesgo.com` | 快速可编辑模板参考 | 课程、教育、课堂展示与快速原型 | 易于快速搭建 | 容易同质化 | `education technology presentation` | 必须 | 使用前检查模板许可和适配 |

## 2. Web/UI 与产品交互

| 来源 | 域名 | 主要用途 | 适用任务 | 优点 | 局限 | 推荐关键词 | 具体案例 | 注意事项 |
|---|---|---|---|---|---|---|---|---|
| Awwwards | `awwwards.com` | 创意视觉、动效、3D 与滚动叙事参考 | 品牌网站、创意官网、整体视觉探索 | 视觉方向强 | 可能视觉优先于实用 | `developer tools`, `data platform`, `editorial` | 必须 | 后台系统不照搬高强度动效 |
| Mobbin | `mobbin.com` | 真实产品结构、状态与流程参考 | Web App、移动端、登录、设置、订阅、Dashboard | 真实产品结构、状态和流程 | 部分内容需登录 | `analytics dashboard`, `onboarding`, `settings` | 必须 | 检查正常、空、错和加载状态 |
| Page Flows | `pageflows.com` | 完整用户操作序列参考 | 注册、支付、购买、预约、升级、搜索流程 | 完整用户操作序列 | 视觉系统不是重点 | `sign up`, `export`, `subscription` | 必须 | 记录步骤、反馈与异常分支 |
| Land-book | `land-book.com` | 全页结构、首屏与 CTA 节奏参考 | Landing Page、SaaS 官网、产品页、首页 | 全页结构与行业案例 | 产品内部流程较少 | `developer tools`, `analytics SaaS` | 必须 | 检查首屏、内容区与 CTA 节奏 |
| Lapa Ninja | `lapa.ninja` | Landing 全页叙事与营销模块参考 | 首屏、社会证明、定价、功能介绍 | 页面节奏清晰 | 可能偏营销模板 | `SaaS analytics`, `open source landing` | 必须 | 用真实内容替换泛化营销模块 |
| SiteInspire | `siteinspire.com` | 排版、克制视觉与品牌风格参考 | 极简、编辑风、作品集、品牌网站 | 排版和克制视觉 | 功能流程证据弱 | `minimal technology`, `editorial web` | 必须 | 适合作为视觉来源而非流程来源 |
| Recent.design | `recent.design` | 当前 Web 趋势与视觉语言参考 | 品牌、字体、图标、动效趋势探索 | 趋势新 | 趋势不等于适用 | `developer product`, `data visualization` | 必须 | 保留行业与可用性边界 |
| Refero | `refero.design` | 页面级 UI 模式与组件参考 | Dashboard 筛选、空状态、表格、产品体验 | 页面级检索细 | 完整流程可能需组合 | `dashboard filter`, `empty state`, `table` | 必须 | 与 Mobbin/Page Flows 交叉验证 |

## 3. Coding Prompt 与 Agent 指令

优先级：官方文档 > 官方 Cookbook/示例 > 高质量开源项目 > 社区聚合。

| 来源 | 域名 | 主要用途 | 适用任务 | 优点 | 局限 | 推荐关键词 | 具体案例 | 注意事项 |
|---|---|---|---|---|---|---|---|---|
| OpenAI 官方文档 | `developers.openai.com` | OpenAI 产品与 Codex 规则的权威依据 | OpenAI、Codex、工具调用、Skills、AGENTS.md | 权威且与产品一致 | 需核对版本 | `Codex skills`, `AGENTS.md`, `tool calling` | 必须 | OpenAI 产品问题优先此来源 |
| Anthropic 官方文档 | `docs.anthropic.com` | Claude 产品与 Agent 规则的权威依据 | Claude、Claude Code、长上下文、工具、CLAUDE.md | 权威提示与 Agent 规则 | 不直接代表 OpenAI 行为 | `Claude Code memory`, `tool use` | 必须 | 只迁移通用规律，标明产品差异 |
| Cursor Directory | `cursor.directory` | 社区项目规则与技术栈指令案例 | Cursor Rules、框架规则、项目指令 | 案例丰富 | 社区质量不一 | `Flask`, `Vue 3`, `testing rules` | 必须 | 与官方框架文档交叉验证 |
| Prompt Engineering Guide | `promptingguide.ai` | 提示工程方法与模式参考 | RAG、Agent、Few-shot、结构化输出 | 方法覆盖广 | 不是产品权威规范 | `agent workflow`, `structured output` | 必须 | 不覆盖官方产品约束 |
| Fabric | `github.com/danielmiessler/fabric` | 可复用 Prompt Pattern 参考 | 分析、总结、审查、模式化任务 | 开源模式可核查 | 场景与目标需适配 | `patterns`, `code review`, `analysis` | 必须 | 检查仓库许可证和具体 pattern |
| 官方 Cookbook | `cookbook.openai.com` | 官方可运行实现案例 | API、结构化输出、工具、缓存、Agent、评估 | 官方可运行示例 | 示例可能随 API 演进 | `agents`, `evals`, `structured outputs` | 必须 | 记录示例日期和适用 API |

## 4. 数据可视化与 Dashboard

| 来源 | 域名 | 主要用途 | 适用任务 | 优点 | 局限 | 推荐关键词 | 具体案例 | 注意事项 |
|---|---|---|---|---|---|---|---|---|
| Apache ECharts Examples | `echarts.apache.org` | 图表实现样式与代码参考 | 折线、雷达、桑基、关系、热力、旭日、大屏 | 实现代码丰富 | 示例不自动保证统计正确 | `graph`, `sankey`, `heatmap`, `ranking` | 必须 | 先选图型再参考样式和代码 |
| From Data to Viz | `data-to-viz.com` | 按数据关系选图并避免误用 | 比较、趋势、相关、网络等图型决策 | 选图逻辑清晰 | 视觉实现有限 | `comparison`, `correlation`, `network` | 必须 | 作为图型 Gate |
| Observable | `observablehq.com` | 可运行高级交互与可视化实验 | D3、地图、时间轴、网络与交互图 | 可运行实验和交互强 | 实施成本可能高 | `network visualization`, `timeline` | 必须 | 评估技术栈和性能成本 |
| D3 Gallery | `d3-graph-gallery.com` | 自定义图表类型与代码参考 | 网络、层级、流、地理、自定义图 | 类型广、代码可读 | 社区示例质量不一 | `network`, `hierarchy`, `flow` | 必须 | 检查许可证与维护状态 |
| Flourish | `flourish.studio` | 快速数据故事与动画表达 | 排名、地图、时间变化、数据故事 | 快速叙事表达 | 导出和授权可能受套餐限制 | `ranking`, `story`, `map` | 必须 | 检查授权与可导出性 |
| Datawrapper | `datawrapper.de` | 严谨新闻图表、标签与表格参考 | 注释图、表格、地图、新闻数据表达 | 简洁严谨 | 高度定制有限 | `annotated chart`, `table`, `map` | 必须 | 借鉴标签和口径，不依赖装饰 |
| Data Viz Project | `datavizproject.com` | 图表类型分类与关系理解 | 分布、组成、比较、关系的图型探索 | 分类直观 | 不等于实现规范 | `distribution`, `composition`, `relationship` | 必须 | 与数据口径和实现来源组合 |

## 5. 科研机制图与系统架构

| 来源 | 域名 | 主要用途 | 适用任务 | 优点 | 局限 | 推荐关键词 | 具体案例 | 注意事项 |
|---|---|---|---|---|---|---|---|---|
| BioRender | `biorender.com` | 科研信息组织与机制视觉参考 | 科研机制、实验流程、Graphical Abstract | 科研信息组织成熟 | 图标和导出受许可约束 | `workflow`, `mechanism`, `graphical abstract` | 必须 | 算法图不机械套生医图标 |
| AWS Architecture Center | `aws.amazon.com` | 完整云参考架构与数据流参考 | 云、数据平台、AI、服务和部署架构 | 参考架构完整 | AWS 服务偏置 | `analytics reference architecture`, `AI workload` | 必须 | 转译为当前技术栈，不照搬服务 |
| Azure Architecture Center | `learn.microsoft.com` | 企业架构边界、质量属性与选型参考 | 企业、数据、安全、AI 与技术选型架构 | 边界和质量属性清晰 | Azure 服务偏置 | `data architecture`, `security`, `AI` | 必须 | 区分通用模式和 Azure 专属组件 |
| Google Cloud Architecture Center | `cloud.google.com` / `docs.cloud.google.com` | 数据流、部署与分析架构参考 | 数据工程、Agent、部署、分析架构 | 数据流案例丰富 | GCP 服务偏置 | `agent architecture`, `data analytics` | 必须 | 转译边界与服务替代关系 |
| Excalidraw Libraries | `libraries.excalidraw.com` | 可编辑架构符号与图标参考 | 软件、Docker、GitHub、云、网络架构图 | 可编辑符号丰富 | 库许可证各异 | `cloud`, `database`, `GitHub`, `Docker` | 必须 | 检查具体图标库许可证 |

科研机制图还应检索相关论文中的真实图例和关系；论文来源按学科数据库或出版平台选择，并记录文献与图号。

## 6. 配色、字体、图标和插画

| 来源 | 域名 | 主要用途 | 适用任务 | 优点 | 局限 | 推荐关键词 | 具体案例 | 注意事项 |
|---|---|---|---|---|---|---|---|---|
| Coolors | `coolors.co` | 色板探索、取色与对比度检查 | 品牌色扩展、配色方案、可访问性色彩 | 快速探索和检查 | 不能替代行业语义 | `technology`, `analytics`, `accessible` | 建议 | 与行业案例和对比度检查组合 |
| Typewolf | `typewolf.com` | 真实字体组合、排版与层级参考 | Web/PPT 字体方案、编辑风排版、层级设计 | 真实排版案例丰富 | 字体可能不可部署 | `sans serif pairing`, `editorial`, `tech` | 必须 | 检查字体许可与环境可用性 |
| Iconify | `iconify.design` | 开源 SVG 图标集与组件入口 | Web/PPT 图标系统、导航、状态和功能图标 | 图标集丰富、接口统一 | 各图标集许可不同 | `lucide`, `tabler`, `material` | 必须 | 记录具体图标集和许可证 |
| unDraw | `undraw.co` | 可改色 SVG 插画参考 | 空状态、产品介绍、Landing Page、PPT | 可改色、易使用 | 容易形成通用模板感 | `analytics`, `empty state`, `developer` | 必须 | 不为填空加入无关插画，检查许可 |
