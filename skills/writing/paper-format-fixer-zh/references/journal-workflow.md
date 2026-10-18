# 期刊稿的格式配置与验收

## 选择依据

学校或期刊的当前官方说明、用户模板、指定样例优先。将其网址、版本、页码和采用的条款写入配置 `sources`，冲突时遵守用户选定的依据；不要把样例中偶然的排版当成规则。

无指定期刊且用户接受通用稿时，选 `general-journal-en.json` 或 `general-journal-zh.json`。它们是本地制定的示范配置：A4、四边 2.54 cm、单栏、黑字、标准字间距 0 pt 与缩放 100%、分层标题、表题在上和图题在下、默认三线表、作者年份引用与悬挂参考文献。英文正文 Times New Roman 12 pt、1.5 倍行距；中文正文宋体 12 pt、固定 24 pt、首行约两字。这些数值不是所有期刊的共同要求，也不冒充 APA 或 GB/T 完整标准。允许依据真实投稿指南替换。

论文类型决定章节：实验研究可用 IMRaD；案例研究、综述、理论论文按其研究问题组织。不要让排版配置强制产生消融、伪代码或实验。

## 配置和语义

`schema_version: 1`、`profile_id`、`label`、`authority`、`language`、`sources` 记录格式身份。`page` 使用 cm；`styles` 按 Word 语义样式定义字体、东亚字体、字号、间距、缩进、对齐与分页；`line_spacing` 表示倍数，`line_spacing_pt` 表示固定磅值，只能二选一。负首行缩进配合左缩进表示悬挂。`character_spacing_pt` 与 `character_scale` 直接检查字符属性。

使用 Title、Abstract Heading、Abstract、Keywords、Heading 1/2/3、Normal、Caption、Table Text、SourceNote、Figure、References Heading、Reference、Footer。现成稿件的普通段落可能混有题注和参考文献；先人工确认语义，必要时提交 `--map`，不要按字体大小或字符串盲目推断全部层级。

```json
{"paragraphs":{"1":"Title","4":"Abstract","69":"Reference"},
 "tables":{"1":{"widths_cm":[7,2,2,4.92]},
           "2":{"kind":"grid","widths_cm":[7.96,7.96]}}}
```

段落号为 `doc.paragraphs` 的 1 起始序号，表号为正文、页眉页脚中全部表的遍历序号；表格例外须说明依据。三线表检查实际 `tcBorders` 及 `tblBorders`，不能只看表样式名。长文字移入正文，表格保留可比较的摘要或数字。表头重复、禁止固定行高、避免一行跨页；无法容纳的长行需拆解内容，不能缩到难读。Caption 遇到紧随的表自动与其保持同页；Figure 与下方 Caption 保持同页。

## 执行入口

通过 workspace dependency loader 取得 Python、Node、Poppler。下文的 `PYTHON` 是它返回的 Python 路径，脚本路径均相对此技能根目录。

1. 原稿审计：`PYTHON scripts/audit_docx_format.py --input input.docx --out before.json`。已选配置时加 `--profile references/general-journal-en.json`，不能把没有配置的概况报告当成通过证明。
2. 保守格式修正：`PYTHON scripts/fix_docx_format.py --input input.docx --profile profile.json --map semantic-map.json --out formatted.docx --report repair.json`。原有 `--rules` 模式仍可使用，但仅覆盖旧模式声明的检查范围。输出须独立于原稿。
3. 新稿：按下述语义块写已完成内容，再运行 `PYTHON scripts/build_manuscript.py --data manuscript.json --profile profile.json --out paper.docx --report build.json`。它生成原生可编辑文字、表格与页码，不负责替写或核实正文。
4. 输出审计：`PYTHON scripts/audit_docx_format.py --input paper.docx --profile profile.json --out audit.json`。结构违规退出码为 1。字体按继承链解析，包含超链接文字；主题字体未解析时不能默认为已通过。核查所选字体在当前机器确实安装。
5. 优先使用 documents 技能的标准渲染器；先读其日志。若 Windows 缺少 LibreOffice 而装有 Word，运行 `scripts/render_docx_word.ps1 -InputDocx paper.docx -OutputDirectory render-v1`。它在新目录对同哈希副本只读导出，不打开或保存作者原稿。失败时记录实际错误，不宣称已视觉验收。
6. 用 Poppler 将真实 PDF 渲染为完整 `page-1.png` 到 `page-N.png`；新版本用新目录。`PYTHON scripts/record_render.py --docx paper.docx --profile profile.json --export render-v1/word-export.json --images render-v1 --out render-v1/render.json` 校验 PDF 全文覆盖、实际字体和所有页图像指纹。其他渲染器需提供等价导出回执，不能伪造 Word 回执。
7. 打开全部页图像并检查正文、题注、图中小字、表格、断页、孤行、裁切、乱码、空白页和参考文献。总览图只用于定位；每页正文需放大阅读。审阅人逐页填写下述记录；程序不会自动宣称“肉眼检查通过”。
8. `PYTHON scripts/verify_release.py --docx paper.docx --profile profile.json --audit audit.json --render render-v1/render.json --visual visual-review.json --out acceptance.json`。只在此配置结构检查和全部实际页均通过时返回 PASS。改动正文、配置、PDF 或任何页图后均须重新验收。

### 稿件块接口

```json
{"blocks":[
  {"style":"Title","text":"Specific research question and subject"},
  {"style":"Subtitle","text":"Generic journal manuscript format demonstration"},
  {"style":"Abstract Heading","text":"Abstract"},
  {"style":"Abstract","text":"Reviewed abstract text"},
  {"style":"Keywords","text":"Keywords: subject; method"},
  {"style":"Heading 1","text":"1 Introduction"},
  {"text":"Reviewed body text"},
  {"type":"table","caption":"Table 1 Indicators","rows":[["Year","Value"],["2025","10"]],"widths_cm":[4,11.92],"note":"Source and units"},
  {"type":"figure","image":"figure.png","caption":"Figure 1 Caption","note":"Source and scope"},
  {"style":"References Heading","text":"References"},
  {"style":"Reference","runs":[{"text":"Verified author and date. "},{"text":"Verified title.","italic":true},{"text":" Source URL","url":"https://example.org"}]}
]}
```

### 逐页记录接口

```json
{"docx_sha256":"current DOCX hash","pdf_sha256":"current PDF hash","reviewer":"actual reviewer",
 "pages":[{"number":1,"sha256":"current page image hash","status":"PASS","notes":"Actual observations on this page"}],
 "resolved_warnings":["table_density:table2"]}
```

只把实际查看的页写 PASS；未查看或存在缺陷写未完成并继续修正。警告解除必须有审阅理由。文件指纹证明版本对应，不能证明学术判断正确，也不能代替真实观看。

## 能力边界与维护

内置 profile 路径支持单栏、普通段落、原生表格、内嵌图片、页眉页脚和超链接。带原生公式、修订、脚注尾注、批注、文本框、外部导入块的稿件返回 BLOCK 并转用保留这些结构的专门模板/OOXML/LaTeX 流程；不能删掉它们来换取通过。双栏、期刊特殊封面、自动编号和复杂浮动对象须增加相应配置与回归样本，不能声称已支持所有期刊。

修改脚本后运行 `PYTHON -m unittest discover -s tests -v`。测试覆盖真实历史缺陷、格式继承、字符属性、三线表、原稿及媒体保护、语义构建入口和过期验收拒绝；再对实际稿件渲染验收。程序测试通过与论文格式通过是两项证据。
