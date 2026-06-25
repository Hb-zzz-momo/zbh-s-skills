---
name: paper-format-fixer-zh
description: "中文论文格式修正技能：用于审计和保守修正 Word .docx 论文、毕业论文、课程论文、期刊投稿稿件的页面设置、页边距、标题样式、正文字体字号、段落间距、表格样式、图表题注、参考文献格式和模板一致性。Use when: 论文格式修正、Word论文排版、毕业论文格式、期刊模板、docx格式检查、图表题注、页边距、标题样式、参考文献格式统一、按学校/期刊模板调整论文。不适用于论文内容创作或学术论证改写（使用 paper-writing-zh）。"
---

# 论文格式修正

## 目标

按用户提供的学校、期刊、会议或课程格式要求，对 Word `.docx` 论文做格式审计、保守修正和模板生成辅助。默认用户模板优先；没有明确规范时只审计并做低风险修复，不套用未知学校或期刊格式。

## 分工

- 内容写作、摘要、引言、方法、实验、结论、润色：使用 `paper-writing-zh`。
- `.docx` 页面、样式、段落、表格、图题、参考文献、模板变量：使用本 skill。
- 引用真实性和参考文献元数据核查：优先结合 Zotero 或 citecheck MCP。

## 工作流

1. **锁定依据**
   - 优先读取用户给的格式要求、模板 `.docx`、样例论文、投稿指南或学校文档。
   - 没有格式依据时，先运行审计脚本，标明“缺少外部格式规范”，只做保守修复。
2. **审计**
   - 运行 `scripts/audit_docx_format.py --input paper.docx --out report.md`。
   - 报告必须列出页面设置、样式、段落异常、表格概况、图表题注线索和参考文献段落线索。
3. **制定规则**
   - 若用户提供明确要求，整理为 `rules.json` 后再修正。
   - 若只有样例模板，优先从模板读取样式和页面设置，避免手写默认值。
4. **保守修正**
   - 运行 `scripts/fix_docx_format.py --input paper.docx --rules rules.json --out paper_formatted.docx`。
   - 默认不覆盖原文件；覆盖必须显式使用 `--overwrite`。
5. **复核**
   - 用 `python-docx` 重新打开输出文件。
   - 必要时再次运行审计脚本，对比修正前后报告。

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

`rules.json` 可包含 `page`、`styles`、`table_style`、`collapse_blank_paragraphs`、`run_font` 等字段。没有规则文件时只执行低风险修复。

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
- 不修改论文内容事实、实验结论或学术 claim。
- 不把 `.docx` 直接改成 `.tex` 或 `.md`，除非用户另行要求。
- 不复制大型第三方源码进 skill；只保留必要规则和可维护脚本。
