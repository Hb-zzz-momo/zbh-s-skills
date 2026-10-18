---
name: paper-format-fixer-zh
description: "论文 Word 排版与格式验收：依据学校或期刊模板审计、修正并渲染检查字体、字间距、段落、图表与参考文献；无指定期刊时可使用明确标注的中英文通用稿配置。Use when: 论文格式、期刊排版、Word论文、三线表、字体字间距、docx格式检查。内容论证由 paper-writing-zh 处理。"
---
# 论文排版与格式验收

<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 决定模式

先锁定用户模板、投稿说明、指定样例及版本，依据优先于此技能默认参数。只请求缺少且影响结果的信息；用户已经接受通用格式时继续完成。

- **原稿保守修复**：没有具体格式依据，也未授权套用新规范时，审计并保守修复，保留原稿身份与结构。
- **按明确模板排版**：提取可执行规则、字体与语义映射，另存新稿。模板有原生公式、脚注、双栏等结构时采用保留模板的专门编辑路径。
- **通用期刊稿示范**：用户无指定期刊且接受通用稿时，使用 `references/general-journal-en.json` 或 `general-journal-zh.json`，稿件和验收注明“通用期刊稿格式示范，非指定期刊模板”。语言按用户需求和原稿确定。

进入配置、构建或正式验收模式时读 [journal-workflow.md](references/journal-workflow.md)，其中包含配置单位、语义块、命令、渲染回执及审阅记录接口。格式参数是配置，不是“所有期刊的标准”。

## 格式验收闭环

1. 保存原稿/配置版本与哈希，检查当前机器字体及文档结构。先审计，再区分内容缺陷与格式缺陷。
2. 明确题名、摘要、关键词、各级标题、正文、图表题注、注释、参考文献等段落角色；旧稿角色混杂时人工映射，避免仅按字号猜测。
3. 用配置修正或语义块构建原生可编辑 DOCX。黑字为此用户的默认偏好，模板/用户指定的颜色优先。检查继承字体、东亚字体、超链接文字，字间距与字符缩放；固定行距和倍数行距分别处理。
4. 修正后重开并运行配置审计；格式修正须保持原文、数据、图片、域和外部链接的内容指纹。表格检查真实边框、列宽、内容密度、重复表头与行分页，不能只看样式名。表题在上、图题在下并控制分页。
5. 通过 documents 的渲染流程导出真实 PDF 和全部页图。Windows 标准渲染器缺少 LibreOffice 时，可使用 `render_docx_word.ps1` 对独立副本只读导出；记录实际渲染器、字体、页数与版本。
6. 逐页打开图片检查，修正后重新渲染。脚本输出、文字提取和总览缩略图不能替代逐页阅读。
7. 运行 `verify_release.py`：结构、渲染、全部页审阅均对应当前 DOCX/配置/PDF/图片且无未解决缺陷才记格式 PASS。旧回执、漏看页、缺渲染或错字体均阻断该声明。

格式 PASS 的范围仅是当前规则与当前渲染版本；研究贡献、来源真实性和投稿适用性分别由内容验收判断。不能说“保证发表”或把通用稿称为已满足某一期刊。

## 工具入口

- `scripts/audit_docx_format.py`：概况审计；加 `--profile` 后执行配置合规检查并记录文件指纹。
- `scripts/fix_docx_format.py`：原有 `--rules` 保守模式；`--profile` 语义格式模式；可用 `--map` 指定角色和表格例外。
- `scripts/build_manuscript.py`：从已审内容的 JSON 语义块创建 Word。
- `scripts/render_docx_word.ps1`、`record_render.py`、`verify_release.py`：只读导出、渲染绑定、最终验收。
- `scripts/render_docx_template.py`：保留现有 docxtpl 模板填充能力，填充后仍须审计与渲染。

使用 workspace dependency loader 提供的运行环境。脚本测试：`PYTHON -m unittest discover -s tests -v`；实际稿仍须真实渲染。

## 支持边界

内置配置路径支持单栏、普通段落、原生表格、内嵌图片、超链接与页眉页脚。原生公式、修订、脚注尾注、批注、文本框和导入块会阻断此路径，转为保持结构的专用流程；不能删去学术内容换取通过。双栏与特殊期刊元素需要对应模板及追加回归样本。

不覆盖原稿；`--overwrite` 只允许覆盖独立输出路径。格式技能不改学术事实或自行补写内容；若需重组或方法纠错，先按用户授权调用 `paper-writing-zh`。交付包含最终 Word、采用规则、内容和格式各自状态；原始材料与审计证据放在现有项目的 evidence/qa，避免进入正文。

## 按需参考

- [journal-workflow.md](references/journal-workflow.md)：正式期刊稿配置与验收。
- [docx-format-workflow.md](references/docx-format-workflow.md)：旧规则兼容模式。
- [python-docx-notes.md](references/python-docx-notes.md)：样式、节、段落与表格接口。
- [docxtpl-template-notes.md](references/docxtpl-template-notes.md)：模板填充注意事项。
