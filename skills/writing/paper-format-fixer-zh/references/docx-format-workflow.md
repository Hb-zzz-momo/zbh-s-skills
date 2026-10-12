# DOCX 论文格式修正流程

本文仅描述原有 `--rules` 兼容模式。正式期刊稿的语义配置、真实边框、有效字体与渲染验收使用 [journal-workflow.md](journal-workflow.md)，不能以本模式的概况检查代替正式验收。

## 输入优先级

1. 用户明确格式文档、学校模板、期刊 author guideline。
2. 用户提供的样例 `.docx` 或模板 `.docx`。
3. 当前论文已有样式和页面设置。
4. 保守通用审计，不做学校/期刊专属推断。

## 审计项目

- 页面：纸张方向、纸张尺寸、上下左右页边距、页眉页脚距离。
- 样式：`Normal`、`Heading 1`、`Heading 2`、`Heading 3`、表格样式。
- 字体颜色：正文、标题、目录、图表题注、表格、参考文献的 run 颜色分布；默认必须显式为 `#000000`。
- 段落：空段、异常字号、异常缩进、段前段后、行距、对齐方式。
- 表格：行列数、空表格、是否有统一样式。
- 图表题注：匹配 `图`、`表`、`Figure`、`Table` 开头的段落。
- 参考文献：匹配 `参考文献`、`References`、`Bibliography` 标题及后续条目线索。

## 修正策略

- 先生成审计报告，再执行修正。
- 有规则文件时，按规则修正页面和样式。
- 没有规则文件时，只做低风险处理：
  - 折叠连续空段。
  - 清理明显异常字号范围外的 run。
  - 将所有文本 run 和常用样式字体颜色显式设为黑色 `#000000`。
  - 保持原有章节结构和正文内容不变。
- 每次修正输出独立新文件；`--overwrite` 仅替换已有独立输出，禁止原路径修改。
- 不允许只完成字号、行距、边距、表格等排版项后就宣称“格式优化完成”；必须复核字体颜色分布。

## 规则 JSON 形状

```json
{
  "page": {
    "top_cm": 2.54,
    "bottom_cm": 2.54,
    "left_cm": 3.0,
    "right_cm": 2.5,
    "header_cm": 1.5,
    "footer_cm": 1.75
  },
  "styles": {
    "Normal": {
      "font_name": "Times New Roman",
      "east_asia_font": "宋体",
      "font_size_pt": 12,
      "font_color": "000000",
      "line_spacing": 1.5,
      "space_before_pt": 0,
      "space_after_pt": 0,
      "first_line_indent_cm": 0.74,
      "alignment": "justify"
    }
  },
  "collapse_blank_paragraphs": true,
  "run_font": {
    "min_pt": 6,
    "max_pt": 36,
    "replacement_pt": 12,
    "font_color": "000000"
  },
  "force_font_color": "000000"
}
```

## 输出要求

- 报告中区分“确定问题”和“需用户格式规范确认”。
- 修正后再次用 `python-docx` 打开输出文件。
- 此分布仅为直接指定颜色；`None` 可能继承为黑色，不能据此直接判为违规。正式格式验收使用 profile 审计解析继承样式并核查超链接文字；再查看真实渲染。
- 最终回复列出输入文件、输出文件、报告文件和未能自动判断的格式项。
