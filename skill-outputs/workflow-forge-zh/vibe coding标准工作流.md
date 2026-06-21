# Vibe Coding 标准工作流（Web Design Skill 组合版）

## 结论

可以用你下载的 Web Design 压缩包组合实现这套工作流，但正确做法不是“同时加载越多 skill 越好”，而是：

> **一个总控 skill 负责分流，每个阶段只加载最适合的一个主 skill。**

优化后的主链是：

```text
需求规格化
-> 选择新建 / 改版 / 图像先行
-> DESIGN.md
-> 审美批判
-> 纵向切片
-> 工程化实现
-> 真实浏览器验收
-> 按需进入正式上线门禁
```

小白可以把它理解成装修：

```text
PRD / Brief       = 先说清楚要装什么房子
DESIGN.md         = 装修图纸和材料表
审美 Skill         = 设计总监检查是不是样板间
纵向切片           = 先装好一个真实房间看方向
前端工程 Skill      = 施工队把整套房子做出来
浏览器验收 Skill    = 验房师检查漏水、开关和尺寸
上线门禁           = 消防、物业、交付和后续维护
```

---

## 1. 压缩包盘点与选择

### 1.1 进入核心工作流

| Skill | 来源 | 作用 | 使用阶段 |
|---|---|---|---|
| `web-design` | `web-design-main.zip` | 从 PRD、URL、截图生成 `DESIGN.md` | 新建网站的设计阶段 |
| `frontend-design` | `skills-main.zip` | 检查设计是否独特、是否有明确 signature | DESIGN.md 编码前 |
| `frontend-ui-engineering` | 本地已安装 | 组件、状态、响应式、可访问性和工程结构 | 编码阶段 |
| `browser-testing-with-devtools` | 本地已安装 | 真实浏览器、控制台、网络和截图验证 | 验收阶段 |
| Vercel Web Interface Guidelines | 远程最新规则 | UI、UX、Accessibility 最终审计 | 验收阶段 |

### 1.2 按场景启用

| Skill | 什么时候用 | 为什么不默认加载 |
|---|---|---|
| `redesign-existing-projects` | 已有网站能运行，但很丑、很像模板或视觉不统一 | 只适用于改版，不适用于从零建站 |
| `imagegen-frontend-web` | 用户明确要求先看视觉稿、参考图 | 规则接近 1000 行，上下文成本高 |
| `image-to-code` | 已经选定视觉稿，需要高还原实现 | 规则超过 1200 行，只在独立阶段使用 |
| `stitch-design-taste` | 用户明确使用 Google Stitch | 工具特定，不应影响普通项目 |
| `web-design-engineer` | 单文件 HTML、交互演示或浏览器视觉产物 | 它不是正式产品工程流程的替代品 |

### 1.3 不进入默认组合

- `design-taste-frontend` 原文件约 1207 行：规则很好，但不适合普通任务整份加载；核心规则已压缩成 Taste Gate。
- `gpt-taste`：强制 GSAP、Bento 等视觉方向，适合实验性页面，不适合作为所有项目默认值。
- `webapp-testing`：和已安装的 `browser-testing-with-devtools` 重复。
- `awesome-claude-design`：是 `DESIGN.md` 灵感目录，不是可执行 skill。
- 约 130 字节且无法打开的 zip：属于无效或下载不完整文件，不进入工作流。

---

## 2. 先选交付级别

### 快速原型

适合：

- 课程项目
- 比赛 Demo
- MVP
- 单页作品集
- 1-7 天内需要展示

目标是“能看、能用、能演示”，不强制完整 CI/CD 和生产监控。

### 正式产品

适合：

- 商业网站
- SaaS
- 学院官网
- 数据平台
- 真实用户长期使用的系统

目标是“可维护、可验收、可预览、可上线、可回滚”。

---

## 3. 再选任务分支

### 分支 A：新建网站

```text
Brief / PRD
-> web-design 生成 DESIGN.md
-> frontend-design + Taste Gate
-> 纵向切片
-> frontend-ui-engineering
-> browser-testing-with-devtools
```

适合：“帮我做一个个人作品集网站。”

### 分支 B：现有页面改版

```text
读取现有代码和截图
-> redesign-existing-projects 做审计
-> 保留功能与技术栈
-> 更新 DESIGN.md
-> 定点修改
-> 浏览器回归验证
```

适合：“这个后台能用，但是太丑了，帮我升级。”

### 分支 C：图像先行

```text
Brief
-> imagegen-frontend-web 生成视觉方向
-> 选定方向
-> image-to-code 分析并实现
-> 反向生成 DESIGN.md
-> 工程化与浏览器验收
```

适合：“先给我看看首页应该长什么样，再写代码。”

### 分支 D：局部 UI Bug

```text
frontend-ui-engineering
-> browser-testing-with-devtools
```

适合：“手机端这个按钮被挤出去了。”

局部问题不要强制重新生成全站 `DESIGN.md`。

---

## 4. 快速原型标准流程

### Step 1：写一页 Brief

最低内容：

```text
网站做什么：个人作品集
给谁看：招聘者和潜在客户
核心动作：查看项目并联系我
页面：主页、项目详情、关于我
风格：克制、专业、有一点编辑感
禁用：紫蓝渐变、三等分功能卡片、廉价毛玻璃
```

完成标准：能回答“给谁、解决什么、演示什么”。

### Step 2：生成 DESIGN.md Lite

包含：

- 视觉主题
- 色彩 token
- 字体层级
- 组件状态
- 布局和间距
- 层级与阴影
- 动效策略
- Do / Don't
- 响应式策略

完成标准：后续代码的颜色、字体、间距和动效都能回到这份文件。

### Step 3：做 Taste Gate

检查：

- 这个设计是否真的适合目标用户？
- 换成另一个项目后是否仍然长得一样？
- Hero 是否表达项目核心？
- 是否有且只有一个主要记忆点？
- 文案是否具体，而不是“提升效率、释放潜能”？

未通过就改 `DESIGN.md`，不要继续写代码。

### Step 4：先做纵向切片

个人作品集可以先做：

```text
导航 + Hero + 第一个代表项目 + 手机端布局
```

不要一开始把主页、项目页、关于页全部写完。先验证一个真实片段，方向错了只返工这一小块。

### Step 5：扩展成可运行首版

- 沿用项目现有框架和组件库。
- 新项目才选择最小可行技术栈。
- 分页面、分 section 小步实现。
- 覆盖 loading、empty、error 和交互状态。
- 不把所有代码塞进一个大文件。

### Step 6：浏览器验收与交付

至少检查：

```text
桌面端
移动端
控制台错误
网络错误
按钮和导航
键盘焦点
文字溢出
元素遮挡
DESIGN.md 一致性
```

交付本地 URL；需要给别人看时再做 Preview Deployment。

---

## 5. 正式产品标准流程

```text
Step 1  产品定义：PRD、用户流、页面结构、数据来源、验收标准
Step 2  设计规范：DESIGN.md、组件状态、内容语气、素材清单
Step 3  技术方案：沿用现有栈，定义路由、数据、测试和部署边界
Step 4  纵向切片：完成一条从 UI 到数据和测试的真实路径
Step 5  增量构建：按页面或用户流小步实现和验证
Step 6  设计验收：DESIGN.md + 桌面/移动浏览器截图
Step 7  Code Review：范围、重复、组件边界、安全和回归风险
Step 8  Preview Deployment：在预览环境复验关键路径
Step 9  上线门禁：性能、Accessibility、SEO、安全、监控、回滚
Step 10 发布与迭代：正式部署，根据真实反馈小步修改
```

与快速原型相比，正式产品多了四样东西：

```text
真实数据链路
自动化测试和 Code Review
Preview Deployment
发布、监控与回滚
```

---

## 6. 为什么不固定技术栈

旧流程直接推荐：

```text
Next.js + TypeScript + Tailwind + shadcn/ui
```

这套组合可以用，但不能变成所有项目的硬规则。

优化后的规则：

1. 已有项目：沿用当前框架、样式方案和组件库。
2. 新项目：根据页面复杂度、数据需求、部署方式选择最小可维护方案。
3. 不因外部 skill 推荐某个库就擅自迁移技术栈。
4. 引入依赖前先查 `package.json` 和官方文档。

例如：

- 一个纯展示活动页，用静态 HTML/CSS/JS 可能更合适。
- 一个复杂 SaaS，可以考虑 Next.js/React 和成熟组件系统。
- 一个已有 Vue 项目，不能因为 AI 熟悉 React 就重写。

---

## 7. 三个小白例子

### 例子 1：个人作品集

你说：

```text
用 web-design-workflow-zh 帮我做个人作品集。
目标用户是招聘者，核心动作是看项目和联系我。
先生成 DESIGN.md，再做 Hero + 一个项目的纵向切片，最后扩展和浏览器验收。
```

Codex 应该做：

```text
一页 Brief
-> DESIGN.md
-> 审美检查
-> Hero + 项目切片
-> 完整页面
-> 手机/桌面验收
```

### 例子 2：已有数据平台太丑

你说：

```text
用 web-design-workflow-zh 的现有改版分支。
不要改业务功能和技术栈，先截图审计，再更新 DESIGN.md 并定点优化。
```

Codex 不应该先重写项目，而应该先列出：

```text
保留什么
哪里像 AI 模板
哪里影响使用
优先改哪三处
如何验证没有破坏原功能
```

### 例子 3：先看视觉稿再开发

你说：

```text
用图像先行分支做产品官网。
先生成每个关键 section 的视觉方向，选定后再 image-to-code，并反向固化 DESIGN.md。
```

关键点是：生成图片不是结束。必须把图片中的色彩、字体、间距、组件和响应式规则写回 `DESIGN.md`。

---

## 8. 阶段门禁

| Gate | 检查证据 | 不通过怎么办 |
|---|---|---|
| G0 需求门 | Brief/PRD 能回答受众、目标、范围 | 补最关键缺口 |
| G1 设计门 | DESIGN.md + Taste Gate | 修改设计，不写代码 |
| G2 切片门 | 真实浏览器截图 + 核心交互 | 只返工切片 |
| G3 构建门 | lint/typecheck/test/build 可用项 | 修复后再扩展 |
| G4 验收门 | 桌面/移动、键盘、控制台、网络 | 修复并复验 |
| G5 发布门 | Preview、性能/SEO/安全/回滚 | 不发布正式环境 |

---

## 9. 标准验收清单

### 产品层

- [ ] 用户一眼知道网站做什么。
- [ ] 页面有明确主要动作。
- [ ] 信息结构服务真实用户任务。

### 设计层

- [ ] 不像通用模板。
- [ ] 字体、颜色、间距和圆角来自 `DESIGN.md`。
- [ ] 只有一个主要 signature moment。
- [ ] 没有文字溢出、元素遮挡和移动端横向滚动。

### 工程层

- [ ] 沿用项目技术栈。
- [ ] 组件职责清楚，没有巨大页面文件。
- [ ] loading、empty、error 和交互状态完整。
- [ ] 可用的 lint、typecheck、test、build 已执行。

### 浏览器层

- [ ] 桌面和移动视口已截图检查。
- [ ] 控制台没有错误。
- [ ] 主要按钮、导航和表单可用。
- [ ] 键盘焦点可见，可访问性基础通过。

### 正式上线层

- [ ] Preview Deployment 可访问。
- [ ] 性能预算和 SEO 要求由项目明确。
- [ ] 无密钥和敏感信息泄漏。
- [ ] 有监控、回滚和发布后检查方式。

---

## 10. 异常处理

| 异常 | 处理方式 |
|---|---|
| 没有 PRD | 快速任务写一页 Brief，正式产品补 PRD |
| 没有设计参考 | 给出 2-3 个差异明确方向，或启用图像先行 |
| 没有真实素材 | 使用真实可替换占位资源并列待替换清单 |
| 用户要求全自动 | Gate 自检后继续，不停在等待确认 |
| 构建环境不可用 | 做静态检查并明确未验证项，不宣称通过 |
| 压缩包打不开 | 标为无效，不凭文件名推断能力 |
| 外部 skill 与项目冲突 | 用户要求和项目约束优先，忽略外部默认偏好 |

---

## 11. 已落地文件

```text
skills/engineering/web-design-workflow-zh/SKILL.md
skills/engineering/web-design-workflow-zh/references/source-map.md
skills/engineering/web-design-workflow-zh/references/workflow-modes.md
skills/engineering/web-design-workflow-zh/references/design-md-contract.md
skills/engineering/web-design-workflow-zh/references/acceptance-checklist.md
skills/engineering/web-design-workflow-zh/scripts/Read-ZipSkill.ps1
```

一句话总结：

> **先用总控 skill 选路线，再用 DESIGN.md 锁方向，用纵向切片降低返工，用工程 skill 做成真项目，最后用浏览器和发布门禁证明它真的能用。**
