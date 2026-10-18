---
name: pptx-builder-zh
description: "PPTX 从零构建技能：使用 PptxGenJS 根据 slide-spec.json 与 PRESENTATION_DESIGN.md 生成原生可编辑的文本、形状、图片、SVG、表格、图表和演讲者备注，并输出源代码、PPTX 与构建几何清单。Use when: 从零生成PPTX、PptxGenJS、可编辑幻灯片、PPT组件化、PPTX源码、构建三页纵向切片。模板编辑请使用 pptx-template-editor-zh。"
---

# PPTX 从零构建
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 前置 Gate

仅在 `slide-spec.json` 已通过叙事 Gate、`PRESENTATION_DESIGN.md` 已通过 Taste Gate、真实数据和素材路径可解析时 Build。缺失项不得编造。先构建三页纵向切片，渲染通过后再构建全套。

## 依赖检查

在本 Skill 目录执行：

```powershell
npm install
npm exec tsx scripts/init-deck.ts -- --help
```

依赖与安装边界见 `references/pptxgenjs-guide.md`。不得假设 Node、字体或图像解码器已存在。

## 构建流程

1. 读取 Slide Contract 和设计令牌。
2. 在 `theme.ts` 中集中定义颜色、字体、尺寸和间距。
3. 用 `components.ts` 复用标题、来源、流程、数据和卡片等组件。
4. 通过 `init-deck.ts` 生成 16:9 PPTX、演讲者备注和几何清单。
5. 用 `check-bounds.ts` 检查越界、最小边距与文字预算。
6. 把 PPTX 交给 `ppt-render-qa-zh`；本 Skill 不自行声明视觉验收完成。

```powershell
npm exec tsx scripts/init-deck.ts -- --spec slide-spec.json --design PRESENTATION_DESIGN.md --assets-root . --output presentation.pptx --manifest build-manifest.json
npm exec tsx scripts/init-deck.ts -- --spec slide-spec.json --design PRESENTATION_DESIGN.md --assets-root . --slides S01,S06,S08 --output slice.pptx --manifest slice-manifest.json
npm exec tsx scripts/check-bounds.ts -- --spec slide-spec.json --manifest build-manifest.json --output build-check.json
```

`PRESENTATION_DESIGN.md` 必须包含 `presentation-theme` JSON 契约；构建器直接解析它，不允许再用独立 `theme.json` 绕开视觉系统。内容块支持原生 chart、table、图片、SVG、文本/形状，输出 manifest 会记录对象计数与实际页面 ID。

## 原生可编辑约束

- 文字、形状、表格和图表尽量使用 PowerPoint 原生对象。
- 照片、插画和必要的 SVG/PNG 可以作为图片；不得把整页截图当内容。
- 不把复杂文本烘焙进图片。
- 颜色、字体、间距必须来自主题令牌，禁止页面内随机硬编码。
- 每页至少有一个有信息意义的视觉对象。
- 连续页面不得重复标题加项目符号或无意义三列卡片。
- 公共组件必须复用；特殊页面仍需登记几何信息。

## 连接语义与容器门禁

流程、架构、机制、课程链路或径向迁移页在构建时必须额外执行以下 Gate：

1. **连接端点**：按节点边界而非节点中心计算起止点；连接线先画、节点后画时，箭头头部必须保留在节点外侧可见区域，不能被后绘制的卡片遮住。
2. **方向语义**：每条有向连接必须有清晰箭头头部。闭环、跨行、回流或径向关系还必须在连线上标注转换动词或约束，例如“标准化”“派发”“反馈”“高敏性”；只有天然按单一阅读顺序排列且无歧义时才可省略。
3. **边界复核**：连接线不得终止于空白、穿过文字或指向不确定的两个节点之间；同一页的箭头方向、线宽和标签位置必须一致。
4. **容器内边距**：卡片文本必须预留明确的左、右、上、下内边距；最后一段文字的可见底边不得进入底部内边距。`fit:'shrink'` 只负责字号降级，不能作为“文本已装入容器”的证据。
5. **高风险清单**：在 manifest 中为每张连接图登记节点数、连接数、带标签连接数和连接方向；为文本卡登记容器框、文本框与最小底部留白。缺少这些记录时，构建结果最高为 `CAUTION`。

构建后必须把所有箭头密集页和全文字最密卡片页交给 `ppt-render-qa-zh` 以原始分辨率检查；不能只看缩小 Montage。

## 错误处理

- 输入 JSON 不合法、页数为空、`slide_id` 重复或输出目录不可写时立即失败。
- 找不到素材时报告具体 slide 与路径，不生成伪素材。
- PptxGenJS 写出失败时保留源文件和错误日志，不把空 PPTX 当成功。
- 边界检查有 `ERROR` 时不得进入 Ship；文字预算 `WARNING` 必须人工复核渲染。
- 自动几何 PASS 不能证明箭头指向正确或文本视觉上未溢出；连接语义、箭头头部可见性与容器底部留白未人工确认时不得进入 Ship。

## 输出与资源

输出可编辑 `.pptx`、TypeScript 源码、依赖锁文件、`build-manifest.json` 和 `build-check.json`。

- PptxGenJS 与安装：`references/pptxgenjs-guide.md`
- 组件契约：`references/component-contract.md`
- 常见故障：`references/common-pitfalls.md`
- 起步项目：`assets/starter/README.md`
