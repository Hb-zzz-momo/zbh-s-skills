---
name: pptx-template-editor-zh
description: "PPTX 模板分析与保守编辑技能：先备份并分析缩略图、文本、页面尺寸、布局、母版、主题、字体和关系文件，再建立内容到模板页面的映射，安全解包、修改、清理孤立媒体并重新打包为新文件。Use when: 基于模板做PPT、修改已有PPTX、替换幻灯片内容、PPTX解包打包、模板布局清单、保留母版主题。"
---

# PPTX 模板编辑
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 不可跳过的顺序

1. 复制原文件并记录 SHA-256；不得覆盖原稿。
2. 先用 `inspect_template.py` 分析尺寸、布局、文本、字体、图片和备注。
3. 先渲染缩略图与 Montage，再理解页面家族。
4. 按 `references/slide-mapping.md` 建立内容到模板页面的映射。
5. 选择保守修改方式：优先 `python-pptx`；只有需要关系级修改时才解包 OOXML。
6. 输出新文件，渲染受影响页并执行全局回归。

不得先改模板再理解其结构。

## 工具

```powershell
python scripts/inspect_template.py template.pptx --json template-analysis.json --markdown template-analysis.md
python scripts/apply_mapping.py template.pptx --mapping mapping.json --output edited.pptx --report edit-report.json
python scripts/unpack.py template.pptx unpacked
python scripts/clean_orphans.py unpacked --report orphan-report.json
python scripts/pack.py unpacked edited.pptx
```

所有脚本支持 `--help`，对路径、ZIP 安全、必要 OOXML 部件和覆盖行为进行检查。

`apply_mapping.py` 支持带 `expected_hits` 的精确文本替换和按图片对象名替换同扩展名媒体；它直接保留未知 OOXML 部件、母版、主题、动画和关系，且强制源文件与输出文件不同并记录源/输出哈希。

## 保留约束

- 保留母版、主题、布局、字体、动画和备注，除非用户明确要求改变。
- 不删除未知关系、嵌入对象、图表工作簿或自定义 XML。
- `clean_orphans.py` 默认只报告；只有人工核对后才用 `--apply` 删除未被任何关系文件提及的媒体。
- 重新打包后必须用真实 Office 打开并渲染，不以 ZIP 合法代替 PPT 合法。
- 内容过多时调整映射或拆页，不把字体缩到不可读。

## 输出

- 原稿备份与哈希记录
- `template-analysis.json/.md`
- `slide-mapping.md`
- 修改后的新 `.pptx`
- 受影响页回归结果与剩余风险

## 资源

- 分析规则：`references/template-analysis.md`
- 页面映射：`references/slide-mapping.md`
- OOXML 风险：`references/xml-editing-risks.md`
