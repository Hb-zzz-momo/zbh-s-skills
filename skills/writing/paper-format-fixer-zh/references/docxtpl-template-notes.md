# docxtpl 模板生成规则

基于 `论文编写/python-docx-template-master.zip` 中 README 和文档提炼。

## 适用场景

- 已有 Word 模板，需要用 JSON 数据批量生成论文封面、声明页、任务书或结构化报告。
- 模板包含页眉页脚、图片、表格、复杂排版，直接在 Word 中维护比代码生成更可靠。

## 基本用法

```python
from docxtpl import DocxTemplate

doc = DocxTemplate("template.docx")
doc.render({"title": "论文题目"})
doc.save("generated.docx")
```

## 模板标签约束

- 普通变量使用 `{{ var }}`。
- 管理整段、表格行、表格列、run 时使用扩展标签：
  - `{%p if condition %}`：段落级。
  - `{%tr for row in rows %}`：表格行级。
  - `{%tc if condition %}`：表格列级。
  - `{%r if condition %}`：run 级。
- 起止标签内侧要保留空格：使用 `{{ var }}`，不要写 `{{var}}`。
- 不要在同一段落、同一行、同一列或同一 run 中重复使用 `{%p`、`{%tr`、`{%tc`、`{%r`。

## 表格和图片

- 横向合并可用 `{% colspan var %}` 或循环中的 `{% hm %}`。
- 纵向合并可用循环中的 `{% vm %}`。
- 单元格背景色标签 `{% cellbg var %}` 必须放在单元格开头。
- 正文图片可用 `InlineImage`；页眉页脚图片通常用占位图再替换。

## 转义

- 默认不自动转义 XML 特殊字符。
- 文本可能包含 `<`、`>`、`&` 时，使用 `|e`、`escape()`、`RichText` 或 `render(..., autoescape=True)`。

## 本 skill 的处理方式

- `render_docx_template.py` 只做模板 + JSON 渲染。
- 如果未安装 `docxtpl`，脚本直接提示安装命令。
- 复杂模板语法错误交给 `docxtpl` 抛出，最终回复中保留错误信息和模板路径。
