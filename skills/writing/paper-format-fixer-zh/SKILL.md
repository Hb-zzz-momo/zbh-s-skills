---
name: paper-format-fixer-zh
description: "中文论文格式修正技能：用于审计和保守修正 Word .docx 论文、毕业论文、课程论文、期刊投稿稿件的页面设置、页边距、标题样式、正文字体字号、字体颜色、段落间距、表格样式、图表题注、参考文献格式和模板一致性。Use when: 论文格式修正、Word论文排版、毕业论文格式、期刊模板、docx格式检查、图表题注、字体颜色、页边距、标题样式、参考文献格式统一、按学校/期刊模板调整论文。不适用于论文内容创作或学术论证改写（使用 paper-writing-zh）。"
---
# 论文格式修正
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 目标

按用户提供的学校、期刊、会议或课程格式要求，对 Word `.docx` 论文做格式审计、保守修正和模板生成辅助。默认用户模板优先；没有明确规范时只审计并做低风险修复，不套用未知学校或期刊格式。

## 分工

- 内容写作、摘要、引言、方法、实验、结论、润色：使用 `paper-writing-zh`。
- `.docx` 页面、样式、字体颜色、段落、表格、图题、参考文献、模板变量：使用本 skill。
- 引用真实性和参考文献元数据核查：优先结合 Zotero 或 citecheck MCP。

## 工作流

1. **锁定依据**
   - 优先读取用户给的格式要求、模板 `.docx`、样例论文、投稿指南或学校文档。
   - 没有格式依据时，先运行审计脚本，标明“缺少外部格式规范”，只做保守修复。
2. **审计**
   - 运行 `scripts/audit_docx_format.py --input paper.docx --out report.md`。
   - 报告必须列出页面设置、样式、字号分布、字体颜色分布、段落异常、表格概况、图表题注线索和参考文献段落线索。
   - 除非用户明确要求彩色或模板强制彩色，字体颜色必须作为硬性检查项：正文、标题、目录、题注、表格、参考文献均应显式写入黑色 `#000000`。
3. **制定规则**
   - 若用户提供明确要求，整理为 `rules.json` 后再修正。
   - 若只有样例模板，优先从模板读取样式和页面设置，避免手写默认值。
   - 本 skill 的默认颜色规则为 `force_font_color: "000000"`；不要把 Word 的“自动颜色”当作已修正。
4. **保守修正**
   - 运行 `scripts/fix_docx_format.py --input paper.docx --rules rules.json --out paper_formatted.docx`。
   - 默认不覆盖原文件；覆盖必须显式使用 `--overwrite`。
5. **复核**
   - 用 `python-docx` 重新打开输出文件。
   - 必须再次运行审计脚本，对比修正前后报告，确认 `字体颜色分布` 只有 `000000`，且没有 `None`、蓝色或其它颜色残留。

## 脚本

### 审计

```powershell
python scripts/audit_docx_format.py --input paper.docx --out report.md
```

输出 Markdown；如果 `--out` 以 `.json` 结尾则输出 JSON。

### 修正

```powershell
python scripts/fix_docx_format.py --input paper.docx --rules rules.json --out paper_formatted.docx
```

`rules.json` 可包含 `page`、`styles`、`table_style`、`collapse_blank_paragraphs`、`run_font`、`force_font_color` 等字段。没有规则文件时只执行低风险修复，并默认把所有文本颜色显式设为黑色 `#000000`。

### 模板生成

```powershell
python scripts/render_docx_template.py --template template.docx --data data.json --out generated.docx
```

此脚本依赖 `docxtpl`。若未安装，提示运行 `python -m pip install docxtpl`。

## 参考资料

- `references/docx-format-workflow.md`：论文格式审计、修正、复核流程。
- `references/python-docx-notes.md`：从 `python-docx-master.zip` 提炼的样式、节、段落、表格规则。
- `references/docxtpl-template-notes.md`：从 `python-docx-template-master.zip` 提炼的模板变量和 Jinja 标签规则。

## 约束

- 不覆盖原论文，除非用户明确要求并使用脚本 `--overwrite`。
- 不内置声称适用于所有学校/期刊的格式默认值。
- 后续默认所有字体颜色全黑；除非用户明确要求彩色或模板强制彩色，不得把标题、封面、目录、题注或参考文献改成其它颜色。
- 不修改论文内容事实、实验结论或学术 claim。
- 不把 `.docx` 直接改成 `.tex` 或 `.md`，除非用户另行要求。
- 不复制大型第三方源码进 skill；只保留必要规则和可维护脚本。
