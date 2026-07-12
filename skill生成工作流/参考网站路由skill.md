# 结论

这个 Skill 不能只是“网站收藏夹”，而应设计成一个**上下文参考路由器**：

```text
识别当前任务
→ 判断需要参考的设计维度
→ 选择对应网站
→ 检索真实案例
→ 提炼可迁移设计规律
→ 组合多个参考来源
→ 转化为当前项目方案
→ 实施并自检
```

下面的提示词按 Codex 当前 Skill 机制设计：使用必需的 `SKILL.md` 描述触发范围和核心工作流，将较长的网站清单、路由矩阵和检索规范放入 `references/`；其中 `description` 是 Codex 隐式判断是否启用 Skill 的关键，因此必须把触发场景和排除场景写清楚。([OpenAI 开发者](https://developers.openai.com/codex/skills "Build skills | ChatGPT Learn"))

---

# 1. 原始需求中需要补强的问题

## 1.1 不能只规定“必须搜索”

只规定必须访问参考网站，可能导致 Codex：

- 每次机械访问同一批网站；
    
- 搜索结果与当前任务无关；
    
- 只浏览首页，没有打开具体案例；
    
- 找到案例但没有落实到最终设计；
    
- 直接模仿单一作品，缺少综合提炼。
    

## 1.2 必须建立任务与网站之间的路由关系

例如：

```text
Web 整体视觉
→ Awwwards + Land-book + Coolors + Typewolf

Web 页面结构
→ Mobbin + Page Flows + Refero + Lapa Ninja

PPT 整套叙事
→ Deck.gallery + Behance + SlideShare

数据图表
→ From Data to Viz + ECharts Examples + Observable

Coding 提示词
→ OpenAI 官方文档 + Anthropic 官方文档 + Cursor Directory

科研机制图
→ BioRender + 云厂商架构中心 + 论文图案例
```

## 1.3 必须形成“参考证据”

Skill 应强制 Codex说明：

1. 查了哪些网站；
    
2. 为什么这些网站适合当前任务；
    
3. 从中提炼了哪些规律；
    
4. 哪些元素被采用；
    
5. 哪些元素被放弃；
    
6. 最终如何转化到当前项目。
    

否则“参考过”无法验收。

---

# 2. 推荐 Skill 名称

```text
contextual-reference-router
```

中文含义：

> 上下文感知型设计参考路由器。

它不只服务于 Web，还可以覆盖：

- PPT；
    
- Web/UI；
    
- Dashboard；
    
- Coding 提示词；
    
- Agent 指令；
    
- 数据可视化；
    
- 科研机制图；
    
- 系统架构图；
    
- 配色、字体、图标与插画。
    

---

# 3. 可直接交给 `$skill-creator` 的完整提示词

使用 `$skill-creator` 创建一个名为 `contextual-reference-router` 的 Codex Skill。

## 一、Skill 的核心目标

该 Skill 用于在 Codex 执行设计、开发、可视化、演示文稿、提示词编写和架构图设计任务之前，主动识别当前任务所需的参考类型，并访问与当前上下文最匹配的高质量参考网站。

该 Skill 不能只是一个静态网站清单。

它必须实现以下完整闭环：

任务理解  
→ 参考需求识别  
→ 网站类型路由  
→ 定向检索  
→ 打开并检查具体案例  
→ 提炼设计规律  
→ 多来源综合  
→ 转化为当前项目方案  
→ 实际执行  
→ 参考落实情况自检

Skill 的最终目的不是让 Codex“看过网站”，而是让 Codex有证据地借鉴高质量案例，并将借鉴内容转化为适合当前任务、当前行业、当前用户和当前技术条件的设计决策。

---

## 二、Skill 触发条件

### 2.1 应当触发

当任务包含以下任一意图时，应自动触发本 Skill：

- 设计、开发或重构网站；
    
- 设计 Landing Page、SaaS 官网、产品官网或活动页面；
    
- 设计后台管理系统、数据平台、Dashboard 或大屏；
    
- 改进 Web 项目的整体视觉、布局、配色、字体或交互；
    
- 设计或优化 PPT、答辩演示、商业汇报、融资路演或课程展示；
    
- 查找 PPT、Web、Dashboard、UI 或报告模板；
    
- 设计数据可视化图表；
    
- 设计科研机制图、算法框架图、流程图、系统架构图或数据流图；
    
- 编写 Coding Prompt、Agent Prompt、Cursor Rules、AGENTS.md、CLAUDE.md 或开发工作流提示词；
    
- 设计品牌视觉、配色方案、字体方案、图标系统或插画风格；
    
- 用户要求作品更加高级、专业、现代、精美、像顶级案例或具有设计感；
    
- 用户要求参考热门网站、优秀案例、行业标杆或竞品；
    
- 当前任务明显会因外部设计参考而提高质量。
    

### 2.2 不应触发

以下任务默认不触发：

- 普通代码报错修复；
    
- 单纯算法实现；
    
- 纯文本翻译；
    
- 简单事实问答；
    
- 仅修改一个变量名或一行代码；
    
- 与视觉、模板、交互、提示词设计无关的普通开发任务；
    
- 用户明确禁止联网或明确要求不参考外部案例；
    
- 已经提供完整参考图，并要求严格按照该参考图进行局部修改，且不需要额外风格探索。
    

### 2.3 边界规则

普通前端功能开发不必自动触发。

但是，只要任务同时涉及以下任一内容，就应触发：

- 页面视觉；
    
- 信息层级；
    
- 交互流程；
    
- 页面模板；
    
- Dashboard 布局；
    
- 图表选型；
    
- 响应式设计；
    
- 色彩和字体；
    
- 用户体验；
    
- 产品展示逻辑。
    

---

## 三、Skill 文件结构

请创建以下结构：

```text
contextual-reference-router/
├── SKILL.md
└── references/
    ├── source-registry.md
    ├── routing-matrix.md
    ├── search-playbook.md
    ├── reference-analysis-template.md
    └── quality-checklist.md
```

默认创建为 instruction-only Skill。

除非确实能够提高检索和验收稳定性，否则不要增加脚本。

---

## 四、SKILL.md 编写要求

`SKILL.md` 必须保持紧凑，主要包含：

1. Skill 的名称和 description；
    
2. 触发条件；
    
3. 核心工作流；
    
4. 强制性规则；
    
5. 对 references 文件的调用说明；
    
6. 最终输出要求；
    
7. 失败和降级处理。
    

不要把全部网站清单直接堆积在 `SKILL.md` 中。

完整网站列表和路由规则应放在 `references/`，减少主 Skill 的上下文占用。

建议使用以下 front matter：

```yaml
---
name: contextual-reference-router
description: Research and synthesize context-appropriate references before creating or redesigning websites, UI, dashboards, presentations, coding-agent prompts, data visualizations, scientific diagrams, architecture diagrams, templates, color systems, or visual assets. Trigger for design, styling, layout, interaction, template selection, visual improvement, prompt-system design, and reference-driven creation. Do not trigger for routine bug fixes, pure factual questions, translation, or non-design coding tasks.
---
```

---

## 五、强制工作流

### 阶段 1：理解当前任务

开始检索前，先识别：

- 最终交付物是什么；
    
- 使用场景是什么；
    
- 目标受众是谁；
    
- 所属行业或主题是什么；
    
- 当前已有技术栈是什么；
    
- 用户明确要求了什么风格；
    
- 哪些内容不能改变；
    
- 是否已有品牌色、模板或参考图；
    
- 当前最需要解决的是视觉、结构、交互、图表还是提示词问题。
    

形成内部任务标签，例如：

```text
交付物：数据分析 SaaS 官网
主要任务：整体视觉与首页结构
行业：开发者工具、开源数据分析
风格：现代、克制、技术感
重点维度：信息架构、配色、字体、首屏、数据展示
```

不得在未理解任务类型的情况下直接打开固定网站。

---

### 阶段 2：识别需要参考的维度

根据当前任务，从以下维度中选择真正需要的部分：

- 内容叙事；
    
- 信息架构；
    
- 页面布局；
    
- 视觉风格；
    
- 配色系统；
    
- 字体层级；
    
- UI 组件；
    
- 用户流程；
    
- 动效；
    
- 图表类型；
    
- 数据标签；
    
- PPT 页面结构；
    
- 科研图信息表达；
    
- 系统架构表达；
    
- Coding Prompt 结构；
    
- Agent 工作流；
    
- 图标和插画；
    
- 模板结构；
    
- 响应式设计；
    
- 可访问性。
    

不得为了完成形式而搜索与任务无关的参考类型。

例如：

- 只设计配色时，不需要浏览大量用户流程网站；
    
- 只设计登录流程时，应优先参考真实产品流程，而不是只浏览视觉获奖网站；
    
- 设计科研机制图时，应优先保证信息准确，而不是追求网页动效；
    
- 编写 Coding Prompt 时，应优先参考官方技术资料，而不是普通提示词聚合站。
    

---

### 阶段 3：参考网站路由

必须读取 `references/routing-matrix.md` 和 `references/source-registry.md`，根据当前任务选择参考源。

每次任务通常选择 2～5 个最相关的网站。

不得无差别访问全部网站。

至少应覆盖两个互补维度，例如：

```text
Web 整体视觉
→ 一个高质量视觉案例网站
→ 一个页面结构网站
→ 一个配色或字体网站

PPT 设计
→ 一个完整 Deck 案例网站
→ 一个高端视觉案例网站
→ 必要时增加数据可视化网站

Dashboard
→ 一个真实产品 UI 网站
→ 一个图表选型网站
→ 一个图表实现案例网站

Coding Prompt
→ 一个官方文档
→ 一个高质量规则或案例库
```

---

### 阶段 4：定向搜索

搜索必须包含当前任务的具体上下文，禁止只搜索过于宽泛的词。

错误示例：

```text
beautiful website
good PPT
dashboard design
coding prompt
```

正确示例：

```text
open source analytics SaaS landing page
AI developer tools dashboard
university data science defense presentation
machine learning research presentation
repository analytics dashboard dark UI
Vue 3 analytics dashboard onboarding
Flask Vue coding agent project rules
multi-objective feature selection mechanism diagram
```

推荐搜索公式：

```text
行业或主题
+ 交付物类型
+ 页面或模块
+ 目标风格
+ 关键功能
```

例如：

```text
developer tools
+ analytics dashboard
+ repository detail page
+ clean dark interface
+ network visualization
```

对于不同网站，应使用适合该网站的关键词，不得机械复制同一个搜索词。

---

### 阶段 5：检查具体案例

不得仅浏览搜索结果标题或网站首页。

存在浏览器、网页搜索、截图或视觉检查工具时，必须尽可能：

1. 打开具体项目或具体案例；
    
2. 检查完整页面或多张页面截图；
    
3. 识别布局、层级、留白、字体、颜色和组件；
    
4. 判断案例是否真的适合当前上下文；
    
5. 排除只有表面风格、但结构不适合的案例。
    

PPT 参考应尽量查看多页，而不是只看封面。

Web 参考应尽量查看首屏、内容区、数据展示区、导航和关键交互。

Dashboard 参考应检查：

- 信息密度；
    
- 卡片结构；
    
- 筛选区；
    
- 图表组合；
    
- 数据标签；
    
- 空状态；
    
- 异常状态；
    
- 响应式表现。
    

如果只能看到文本摘要，必须明确说明视觉检查受到限制，不能假装已经完整查看案例。

---

### 阶段 6：建立参考分析表

每个被采用的参考案例都应记录：

```text
参考来源：
具体案例或页面：
适合当前任务的原因：
主要观察维度：
可借鉴元素：
不适合直接采用的元素：
向当前项目的转化方式：
```

不得只记录“这个网站很好看”。

需要提炼为可执行规则，例如：

错误：

```text
参考了一个高级 SaaS 网站。
```

正确：

```text
参考案例采用大字号左对齐标题、短副标题和右侧产品界面预览，
首屏只保留一个主操作按钮。
当前项目将沿用这种信息层级，
但会把产品截图替换为 OpenRank 关系网络与健康度趋势组合，
避免形成普通 SaaS 模板感。
```

---

### 阶段 7：多来源综合

禁止直接复制单个案例。

通常应从 2～4 个互补参考中分别提取：

- 一个案例的信息结构；
    
- 一个案例的视觉语言；
    
- 一个案例的配色或字体；
    
- 一个案例的交互方式；
    
- 一个案例的图表表达。
    

然后根据当前项目重新组合。

必须区分：

```text
借鉴设计规律
≠ 复制具体作品
```

不得直接照搬：

- 品牌名称；
    
- 商标；
    
- 专有插画；
    
- 受版权保护的视觉素材；
    
- 完整页面构图；
    
- 原始文案；
    
- 私有代码；
    
- 未确认授权的模板资源。
    

导入模板、字体、图标、插画或代码之前，必须检查许可证和使用条件。

---

### 阶段 8：设计转译

检索完成后，先形成简短的 Reference Brief，再执行设计或编码。

Reference Brief 至少包含：

```text
1. 当前设计目标
2. 选取的参考类型
3. 核心参考来源
4. 提炼出的设计规律
5. 应用于当前任务的具体方式
6. 明确不采用的设计模式
```

例如：

```text
设计目标：
为开源生态数据分析平台设计克制、可信、现代的视觉体系。

参考组合：
Land-book 用于首页结构；
Mobbin 用于产品内部页面；
Coolors 用于配色；
ECharts Examples 用于关系图和趋势图。

设计转译：
首页采用清晰的单主线叙事；
内部页面提高信息密度；
色彩以深蓝灰为基础，绿色只表示健康和增长；
图表避免装饰性渐变，突出数值比较和异常状态。
```

只有完成该阶段，才进入实际创作。

---

### 阶段 9：执行任务

执行过程中，必须将参考规律落实到具体产物。

不同任务的落实方式包括：

#### Web

- 页面信息架构；
    
- 栅格布局；
    
- 首屏结构；
    
- 导航；
    
- 内容节奏；
    
- UI 组件；
    
- 配色变量；
    
- 字体层级；
    
- 间距系统；
    
- 交互状态；
    
- 响应式规则。
    

#### PPT

- 整体叙事；
    
- 目录层级；
    
- 页面节奏；
    
- 封面；
    
- 章节页；
    
- 图文比例；
    
- 数据页；
    
- 对比页；
    
- 总结页；
    
- 母版样式。
    

#### Dashboard

- 指标卡片；
    
- 筛选区；
    
- 图表组合；
    
- 主次信息；
    
- 颜色语义；
    
- 异常提醒；
    
- 数据标签；
    
- 空状态；
    
- 加载状态。
    

#### Coding Prompt

- 角色；
    
- 目标；
    
- 输入；
    
- 上下文；
    
- 工作流；
    
- 工具调用规则；
    
- 约束；
    
- 验收标准；
    
- 失败处理；
    
- 输出格式；
    
- 自检清单。
    

#### 科研图和架构图

- 信息层级；
    
- 数据流；
    
- 模块关系；
    
- 箭头语义；
    
- 图例；
    
- 颜色编码；
    
- 输入输出；
    
- 闭环关系；
    
- 模型边界；
    
- 关键创新点。
    

---

### 阶段 10：参考落实自检

完成任务后，必须检查：

- 是否根据任务上下文选择了网站；
    
- 是否访问了具体案例，而非只看首页；
    
- 是否至少使用了两个互补参考来源；
    
- 是否解释了每个来源的相关性；
    
- 是否提炼了可执行规律；
    
- 是否把规律落实到最终产物；
    
- 是否避免直接复制单个案例；
    
- 是否保持当前项目的品牌和内容特征；
    
- 是否检查了素材许可证；
    
- 是否存在为了“高级感”而牺牲可读性的问题；
    
- 是否存在视觉漂亮但功能不完整的问题；
    
- 是否存在参考网站与当前行业不匹配的问题；
    
- 是否说明了无法联网或无法视觉检查的限制；
    
- 是否区分事实、观察、推断和设计建议。
    

如果没有完成参考检索与设计转译，不得声称“已参考行业优秀案例”。

---

## 六、网站参考源注册表

将以下内容整理到 `references/source-registry.md`。

每个网站必须记录：

- 网站名称；
    
- 域名；
    
- 主要用途；
    
- 适用任务；
    
- 优点；
    
- 局限；
    
- 推荐搜索关键词；
    
- 是否需要重点查看具体案例；
    
- 使用时的注意事项。
    

### 6.1 PPT 与演示文稿

#### Deck.gallery

域名：`deck.gallery`

适合：

- 完整商业 Deck；
    
- 产品发布；
    
- 融资路演；
    
- 品牌手册；
    
- 商业演示；
    
- PPT 整体叙事。
    

重点借鉴：

- 页面顺序；
    
- 信息密度；
    
- 页面节奏；
    
- 章节衔接；
    
- 数据页；
    
- 封面和结尾。
    

#### Behance

域名：`behance.net`

适合：

- 高端 Presentation Design；
    
- 品牌视觉；
    
- 科技风 PPT；
    
- 课程答辩视觉；
    
- 科研汇报；
    
- 完整设计项目。
    

重点借鉴：

- 视觉语言；
    
- 字体搭配；
    
- 图文比例；
    
- 页面连续性；
    
- 品牌一致性。
    

#### SlideShare

域名：`slideshare.net`

适合：

- 完整演讲结构；
    
- 真实商业和教育内容；
    
- 论证逻辑；
    
- 目录与故事线。
    

重点借鉴：

- 内容结构；
    
- 演讲节奏；
    
- 信息组织。
    

不得将其作为高端视觉的唯一来源。

#### Pitch

域名：`pitch.com`

适合：

- 商业汇报模板；
    
- SaaS；
    
- 产品介绍；
    
- 市场方案；
    
- 项目计划。
    

#### Dribbble

域名：`dribbble.com`

适合：

- PPT 单页视觉；
    
- 封面；
    
- 数据页面；
    
- UI 局部灵感。
    

限制：

- 部分案例只有单页；
    
- 不适合作为完整叙事的唯一来源。
    

#### Slidesgo

域名：`slidesgo.com`

适合：

- 可编辑 PPT 模板；
    
- 课程汇报；
    
- 教育演示；
    
- 快速搭建。
    

使用前检查模板授权和适配程度。

---

### 6.2 Web、UI 与产品交互

#### Awwwards

域名：`awwwards.com`

适合：

- 顶级创意网站；
    
- 品牌官网；
    
- 动效；
    
- 3D；
    
- 滚动叙事；
    
- 高级视觉方向。
    

限制：

- 部分作品视觉优先于实用性；
    
- 后台系统不应直接照搬其高强度动效。
    

#### Mobbin

域名：`mobbin.com`

适合：

- 真实产品 UI；
    
- Web App；
    
- 移动端；
    
- 登录注册；
    
- 设置；
    
- 搜索；
    
- 订阅；
    
- Dashboard；
    
- 产品内部页面。
    

重点借鉴：

- 真实产品结构；
    
- 状态设计；
    
- 组件布局；
    
- 用户流程。
    

#### Page Flows

域名：`pageflows.com`

适合：

- Onboarding；
    
- 登录注册；
    
- 支付；
    
- 购买；
    
- 预约；
    
- 升级；
    
- 搜索；
    
- 用户操作流程。
    

#### Land-book

域名：`land-book.com`

适合：

- Landing Page；
    
- SaaS 官网；
    
- 产品页；
    
- 作品集；
    
- 电商首页；
    
- 首页整体结构。
    

#### Lapa Ninja

域名：`lapa.ninja`

适合：

- Landing Page 全页结构；
    
- 首屏；
    
- 内容区节奏；
    
- CTA；
    
- 社会证明；
    
- 定价区域；
    
- 产品功能介绍。
    

#### SiteInspire

域名：`siteinspire.com`

适合：

- 极简网站；
    
- 品牌网站；
    
- 编辑风；
    
- 排版；
    
- 作品集。
    

#### Recent.design

域名：`recent.design`

适合：

- 当前 Web 视觉趋势；
    
- 品牌；
    
- 字体；
    
- 图标；
    
- 动效；
    
- 产品设计。
    

#### Refero

域名：`refero.design`

适合：

- 具体页面；
    
- UI 模式；
    
- 组件；
    
- 产品体验；
    
- 页面级检索。
    

---

### 6.3 Coding Prompt 与 Agent 指令

该分类的优先级必须是：

```text
官方文档
> 官方 Cookbook 或示例
> 高质量开源项目
> 社区聚合网站
```

#### OpenAI 官方 Prompt Engineering 文档

域名：`developers.openai.com`

适合：

- OpenAI 模型提示词；
    
- Codex 指令；
    
- 工具调用；
    
- 输出约束；
    
- Agent 工作流；
    
- Skills；
    
- AGENTS.md。
    

#### Anthropic 官方文档

域名：`docs.anthropic.com`

适合：

- Claude；
    
- Claude Code；
    
- 长上下文；
    
- XML 结构；
    
- Agent 指令；
    
- CLAUDE.md；
    
- 工具使用。
    

#### Cursor Directory

域名：`cursor.directory`

适合：

- Cursor Rules；
    
- 技术栈规则；
    
- 前端和后端项目规范；
    
- 框架级提示词；
    
- Agent 项目指令。
    

限制：

- 社区内容质量不完全一致；
    
- 需要与官方框架文档交叉验证。
    

#### Prompt Engineering Guide

域名：`promptingguide.ai`

适合：

- 提示词工程方法；
    
- RAG；
    
- Agent；
    
- Few-shot；
    
- 结构化输出；
    
- 提示词模式。
    

#### Fabric

项目：`danielmiessler/fabric`

适合：

- 可复用 Prompt Pattern；
    
- 分析；
    
- 总结；
    
- 写作；
    
- 代码审查；
    
- 研究工作流。
    

#### 官方 Cookbook

适合：

- API 示例；
    
- 结构化输出；
    
- 工具调用；
    
- Prompt Caching；
    
- Agent 实现；
    
- 自动评估。
    

---

### 6.4 数据可视化与 Dashboard

#### Apache ECharts Examples

域名：`echarts.apache.org`

适合：

- 图表实现；
    
- 折线图；
    
- 雷达图；
    
- 桑基图；
    
- 关系图；
    
- 热力图；
    
- 旭日图；
    
- 动态排名；
    
- 大屏图表。
    

#### From Data to Viz

域名：`data-to-viz.com`

适合：

- 根据数据类型选择图表；
    
- 判断图表是否适合；
    
- 避免常见误用。
    

#### Observable

域名：`observablehq.com`

适合：

- D3；
    
- 高级交互式图表；
    
- 地图；
    
- 时间轴；
    
- 实验性可视化。
    

#### D3 Gallery

适合：

- 高度自定义图表；
    
- 网络图；
    
- 层级图；
    
- 流图；
    
- 地理图。
    

#### Flourish

域名：`flourish.studio`

适合：

- 数据故事；
    
- 动态图表；
    
- 排名动画；
    
- 新闻可视化；
    
- 地图。
    

#### Datawrapper

域名：`datawrapper.de`

适合：

- 简洁、严谨的数据表达；
    
- 新闻图表；
    
- 表格；
    
- 地图；
    
- 数据标签。
    

#### Data Viz Project

域名：`datavizproject.com`

适合：

- 查找图表类型；
    
- 理解不同数据关系的可视化方式。
    

---

### 6.5 科研机制图和系统架构图

#### BioRender

域名：`biorender.com`

适合：

- 科研机制图；
    
- 实验流程；
    
- Graphical Abstract；
    
- 层次结构；
    
- 论文配图。
    

注意：

- 不得机械套用生物医学图标风格；
    
- 算法机制图应借鉴信息组织，不应强行加入无意义图标。
    

#### AWS Architecture Center

域名：`aws.amazon.com`

适合：

- 云架构；
    
- 数据平台；
    
- AI 系统；
    
- 服务关系；
    
- 部署架构。
    

#### Azure Architecture Center

域名：`learn.microsoft.com`

适合：

- 企业架构；
    
- 参考架构；
    
- 数据流程；
    
- 安全设计；
    
- 技术选型。
    

#### Google Cloud Architecture Center

域名：`cloud.google.com` 或 `docs.cloud.google.com`

适合：

- 数据工程；
    
- AI Agent；
    
- 云服务；
    
- 系统部署；
    
- 数据分析架构。
    

#### Excalidraw Libraries

域名：`libraries.excalidraw.com`

适合：

- 软件架构；
    
- Docker；
    
- GitHub；
    
- 云服务；
    
- 网络；
    
- 服务组件。
    

---

### 6.6 配色、字体、图标和插画

#### Coolors

域名：`coolors.co`

适合：

- 配色生成；
    
- 从图片提取色彩；
    
- 色板；
    
- 对比度检查；
    
- 品牌色扩展。
    

#### Typewolf

域名：`typewolf.com`

适合：

- 字体组合；
    
- Web 排版；
    
- 标题和正文字体；
    
- 字体趋势。
    

#### Iconify

域名：`iconify.design`

适合：

- 开源图标；
    
- SVG；
    
- 前端图标组件；
    
- 图标风格统一。
    

必须检查具体图标集许可证。

#### unDraw

域名：`undraw.co`

适合：

- SVG 插画；
    
- 网站空状态；
    
- 产品介绍；
    
- PPT 配图。
    

不得为了填充页面而加入与内容无关的装饰插画。

---

## 七、任务路由矩阵

将以下规则整理到 `references/routing-matrix.md`。

### 7.1 Web 整体视觉

优先：

```text
Awwwards
+ Land-book
+ SiteInspire 或 Recent.design
+ Coolors
+ Typewolf
```

### 7.2 Landing Page 页面结构

优先：

```text
Land-book
+ Lapa Ninja
+ Awwwards
```

### 7.3 Web App 或后台系统

优先：

```text
Mobbin
+ Refero
+ Page Flows
```

### 7.4 Web 用户流程

优先：

```text
Page Flows
+ Mobbin
```

### 7.5 Dashboard

优先：

```text
Mobbin
+ From Data to Viz
+ Apache ECharts Examples
+ Observable
```

### 7.6 PPT 整体结构

优先：

```text
Deck.gallery
+ SlideShare
+ Pitch
```

### 7.7 PPT 高端视觉

优先：

```text
Behance
+ Deck.gallery
+ Dribbble
```

### 7.8 科研汇报 PPT

优先：

```text
Behance
+ Deck.gallery
+ SlideShare
+ From Data to Viz
```

### 7.9 Coding Prompt

优先：

```text
OpenAI 官方文档
+ 对应模型或工具的官方文档
+ 官方 Cookbook
+ Cursor Directory 或 Fabric
```

### 7.10 Cursor Rules、AGENTS.md 或 CLAUDE.md

优先：

```text
对应产品官方文档
+ Cursor Directory
+ 高质量开源仓库实例
```

### 7.11 数据可视化

优先顺序：

```text
From Data to Viz
→ Data Viz Project
→ ECharts Examples
→ Observable 或 D3 Gallery
→ Flourish 或 Datawrapper
```

先确定图表类型，再参考视觉表现和代码实现。

### 7.12 科研机制图

优先：

```text
BioRender
+ Behance 科研图案例
+ 相关论文中的真实机制图
```

准确性优先于装饰性。

### 7.13 系统架构图

优先：

```text
AWS Architecture Center
+ Azure Architecture Center
+ Google Cloud Architecture Center
+ Excalidraw Libraries
```

### 7.14 配色设计

优先：

```text
当前行业优秀案例
+ Coolors
+ 对比度检查
```

不得脱离项目行业，仅根据个人喜好选择色板。

### 7.15 字体设计

优先：

```text
Typewolf
+ 当前参考网站的真实排版
+ 项目部署环境中实际可用字体
```

---

## 八、检索数量控制

Skill 必须避免无休止研究。

普通任务建议：

- 选择 2～5 个网站；
    
- 查看 3～8 个具体案例；
    
- 最终保留 2～4 个核心参考；
    
- 提炼 3～7 条可执行设计规律。
    

大型任务可以增加参考数量，但只有在新来源能够补充新的设计维度时才继续搜索。

当后续案例已经无法提供新的信息时，应停止检索并进入执行阶段。

---

## 九、失败和降级处理

### 9.1 无法联网

如果当前环境不能访问外部网站：

- 明确说明无法完成实时参考检索；
    
- 不得虚构已经访问过某个网站；
    
- 检查项目中是否存在本地截图、模板、设计规范或历史案例；
    
- 可以基于已有知识提出暂定方案；
    
- 必须把“实时参考检索未完成”列为限制。
    

### 9.2 网站无法访问

如果某个网站无法打开：

- 选择同类别替代网站；
    
- 不要因单个网站不可用而停止整个任务；
    
- 记录替代原因。
    

### 9.3 搜索结果质量低

如果搜索结果与任务不匹配：

- 调整行业词；
    
- 调整页面类型；
    
- 增加功能关键词；
    
- 增加风格关键词；
    
- 更换参考网站；
    
- 不得强行使用不相关案例。
    

### 9.4 用户要求快速执行

即使用户要求快速执行，也应完成最小参考流程：

```text
识别任务
→ 选择两个最相关来源
→ 提炼三条设计规律
→ 执行
```

除非用户明确要求跳过外部参考。

---

## 十、最终反馈格式

在最终交付说明中，增加一个简洁的“参考依据”部分。

不要展示冗长思维过程，只展示可以被核查的结果：

```text
## 参考依据

- 参考来源：网站或具体案例
- 选择原因：为什么适合当前任务
- 提炼规律：布局、配色、字体、交互或叙事
- 实际应用：这些规律落实到了哪些页面、组件或设计决策
- 未采用内容：哪些常见做法因不适合当前项目而被排除
```

如果用户只需要最终产物，该部分保持简短，但不得完全省略参考证据。

---

## 十一、质量检查清单

将以下检查项写入 `references/quality-checklist.md`：

### 任务适配

- 参考网站是否与当前任务类型匹配；
    
- 参考案例是否与当前行业匹配；
    
- 是否考虑目标用户；
    
- 是否考虑技术栈和实施成本。
    

### 检索质量

- 是否打开了具体案例；
    
- 是否避免只看搜索摘要；
    
- 是否使用了多个互补来源；
    
- 是否停止了无效重复检索。
    

### 提炼质量

- 是否提炼为可执行规律；
    
- 是否区分结构、视觉、交互和内容；
    
- 是否说明采用和不采用的原因；
    
- 是否避免使用“高级、精美、现代”等空泛表述。
    

### 转化质量

- 是否结合当前项目重新设计；
    
- 是否避免直接复制；
    
- 是否将参考落实到具体代码或产物；
    
- 是否保留当前项目独有的信息和品牌特征。
    

### 合规质量

- 是否检查素材和模板许可证；
    
- 是否避免复制品牌资产；
    
- 是否避免虚构访问记录；
    
- 是否明确说明访问限制。
    

---

## 十二、Skill 验收测试

创建 Skill 后，至少使用以下测试任务进行验证。

### 测试一：Web 整体视觉

输入：

```text
为一个面向开发者的开源生态数据分析平台设计官网整体视觉和首页。
```

预期：

- 自动触发 Skill；
    
- 选择 Web、配色、字体相关参考网站；
    
- 不应优先访问 PPT 网站；
    
- 输出 Reference Brief；
    
- 将参考落实到首页结构、配色、字体和数据展示中。
    

### 测试二：Web 用户流程

输入：

```text
设计注册、登录、收藏项目和导出报告的完整交互流程。
```

预期：

- 优先使用 Mobbin、Page Flows 或 Refero；
    
- 不应主要使用 Awwwards；
    
- 输出状态、异常、空状态和反馈机制。
    

### 测试三：PPT

输入：

```text
重新设计一个数据科学课程答辩 PPT，使其具有专业科技感。
```

预期：

- 使用 Deck.gallery、Behance、SlideShare 等来源；
    
- 同时参考数据可视化网站；
    
- 关注整套叙事，而不是只设计封面。
    

### 测试四：Coding Prompt

输入：

```text
为 Flask、Vue 3 项目编写可长期复用的 Codex 开发 Skill。
```

预期：

- 优先查阅 OpenAI 官方文档；
    
- 补充高质量项目规则案例；
    
- 不应使用 Web 视觉网站作为主要来源。
    

### 测试五：Dashboard

输入：

```text
设计一个 GitHub 开源项目健康度分析 Dashboard。
```

预期：

- 使用真实产品 UI、图表选型和图表实现三类参考；
    
- 检查指标卡片、筛选、趋势、关系网络和风险状态；
    
- 不得只搜索“漂亮 Dashboard”。
    

### 测试六：科研机制图

输入：

```text
设计一个多目标特征选择算法的科研机制图。
```

预期：

- 优先保证算法关系和信息准确；
    
- 参考科研机制图和架构表达；
    
- 不得机械套用 SaaS 或 Landing Page 风格。
    

### 测试七：不应触发

输入：

```text
修复 Python 函数中的数组越界问题。
```

预期：

- 不自动触发本 Skill；
    
- 直接执行代码排错流程。
    

---

## 十三、最终创建要求

完成 Skill 后：

1. 展示最终目录结构；
    
2. 输出完整 `SKILL.md`；
    
3. 输出全部 references 文件；
    
4. 检查 front matter 是否有效；
    
5. 检查 description 是否能够准确隐式触发；
    
6. 检查排除场景是否明确；
    
7. 使用上述测试用例模拟触发结果；
    
8. 修复错误触发、漏触发或网站路由不准确的问题；
    
9. 保证所有规则真实可执行；
    
10. 不得只生成一个简单的网站列表。
    

---

# 4. 这个版本的主要改进

## 4.1 从“网站库”升级为“参考决策系统”

Skill 不会每次都打开相同网站，而是先判断：

```text
当前做什么
→ 需要参考什么
→ 哪类网站最有价值
```

## 4.2 加入强制参考闭环

它要求 Codex 完成：

```text
找到案例
→ 提炼规律
→ 解释适用性
→ 转化到项目
→ 检查是否真正落实
```

## 4.3 区分不同类型的网站价值

例如 Awwwards 适合整体视觉，但不一定适合后台产品流程；Mobbin 适合真实 UI，却不一定适合 PPT 叙事。Skill 会根据任务进行组合，而不是根据网站知名度机械选择。

## 4.4 防止“假装参考”

通过强制记录：

- 具体来源；
    
- 具体案例；
    
- 采用元素；
    
- 放弃元素；
    
- 转化方式；
    

可以减少只说“参考了优秀案例”但没有证据的情况。

## 4.5 控制研究成本

设置了正常情况下的检索范围：

```text
2～5 个网站
3～8 个具体案例
2～4 个核心参考
3～7 条设计规律
```

避免 Codex 在参考阶段投入过多时间，却迟迟不进入实际执行。

---
