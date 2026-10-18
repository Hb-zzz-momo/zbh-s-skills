# python-docx 使用边界

基于 `论文编写/python-docx-master.zip` 中 README 和用户文档提炼。

## 能稳定处理

- 打开、读取、保存 `.docx`。
- 读取和修改 sections：页边距、页眉页脚距离、纸张尺寸、方向。
- 读取和修改段落样式、字符样式、表格样式。
- 设置字体、字号、粗体、斜体、下划线、段前段后、缩进、行距、对齐。
- 遍历段落、runs、表格、行、单元格。

## 样式注意事项

- 内置样式在 OOXML 中使用英文名，如 `Normal`、`Heading 1`。
- 中文 Word UI 中看到的本地化样式名不等于内部样式名。
- 自定义样式按 Word UI 中的实际名称访问。
- 修改 style 会影响使用该 style 的内容；直接修改 run 只影响局部文本。

## Section 注意事项

- 多数论文只有一个 section，但脚本应遍历所有 section。
- 页边距使用 EMU；脚本中用 `docx.shared.Cm`、`Inches`、`Pt` 转换。
- 横向页面需要同时调整 `orientation`、`page_width`、`page_height`。

## 低层 XML 需求

- `python-docx` 对中文字体 eastAsia 支持有限，需要通过 OOXML 设置 `w:eastAsia`。
- 删除段落没有高层 API，可通过 `_element.getparent().remove(_element)` 实现。
- 这些低层操作必须局限在明确、可测试的小函数里。

## 不要依赖它做的事

- 不要指望它完整保留复杂域代码、目录、交叉引用和批注语义。
- 不要用它判断学校或期刊规范是否正确；它只能读写文档结构。
- 不要把内容语义修改混入格式修正脚本。
