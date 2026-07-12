---
name: ppt-render-qa-zh
description: "PPTX 渲染、内容、几何、图片与视觉质检技能：把 PPTX 转为 PDF 和逐页图片，生成 Montage，提取全文，检查越界、裁切、低分辨率、占位文本、跨页一致性与信息节奏，记录问题并强制完成至少一轮修复复验。Use when: PPT渲染、PPT验收、Montage、文字溢出、元素越界、PPTX转图片、qa-report.md、修复后复验。"
---

# PPT 渲染与修复复验
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 完成定义

首次生成结果不能声明完成。必须完成：

```text
首次渲染 → 问题记录 → 实际修复 → 重新生成
        → 重新渲染 → 受影响页复查 → 全局 Montage 复查
```

若首次自动检查没有发现问题，仍须人工以“找缺陷”视角检查 Montage 和代表页，并记录检查结论；不得把零问题当作免修复理由。

## Step 1：检查依赖

```powershell
python scripts/render_slides.py --help
python scripts/make_montage.py --help
python scripts/extract_text.py --help
```

渲染后端自动按 LibreOffice → Microsoft PowerPoint → WPS Office 选择，并在 manifest 中记录实际后端。PDF 转图优先使用 Poppler `pdftoppm`。缺失时给出明确安装命令，不假设环境已具备。

## Step 2：首次 QA

```powershell
python scripts/render_slides.py presentation.pptx qa/pass1/render --backend auto
python scripts/make_montage.py qa/pass1/render/slides qa/pass1/montage.png
python scripts/extract_text.py presentation.pptx --markdown qa/pass1/text.md --json qa/pass1/text.json
python scripts/check_geometry.py presentation.pptx --output qa/pass1/geometry.json
python scripts/check_image_resolution.py presentation.pptx --output qa/pass1/images.json
python scripts/check_charts.py presentation.pptx --output qa/pass1/charts.json --min-charts 1
python scripts/check_contrast.py presentation.pptx --output qa/pass1/contrast.json
python scripts/check_office_layout.py presentation.pptx --output qa/pass1/office-layout.json --expected-font "Microsoft YaHei"
```

按 `references/acceptance-checklist.md` 人工检查逐页图片与 Montage。自动检查不能证明不存在遮挡、字体替换或视觉节奏问题。

## Step 3：记录与修复

按 `references/qa-severity-levels.md` 记录 slide、严重度、问题、证据、修复动作与责任源文件。修复源代码或模板映射，不在导出的 PDF/图片上打补丁。

## Step 4：复验

对修复后的新 PPTX 重复完整命令。受影响页需逐页比较，全套需 Montage 回归。用 `build_qa_report.py` 汇总 pass1 与 pass2：

```powershell
python scripts/build_qa_report.py --render qa/pass2/render/render-manifest.json --text qa/pass2/text.json --geometry qa/pass2/geometry.json --images qa/pass2/images.json --extra qa/pass2/charts.json --extra qa/pass2/contrast.json --extra qa/pass2/office-layout.json --manual-review qa/pass2/manual-review.json --previous qa/pass1/geometry.json --output qa/qa-report.md --fix-log qa/fix-log.md
```

没有符合 `assets/manual-review-template.json` 的人工复核记录时，汇总结论最多为 `CAUTION`，脚本返回非零；不得用未勾选的 Markdown 清单冒充人工验收。

## Ship Gate

- `BLOCK`：Office 无法打开/渲染、元素越界、文字裁切、关键内容缺失、图表数据错误。
- `CAUTION`：低分辨率非关键图片、轻微节奏或密度问题、有说明的字体替代。
- `PASS`：阻断项归零，修复复验有证据，剩余风险已记录。

## 输出

- PDF、逐页图片、Montage。
- 文本、几何与图片检查 JSON。
- `qa-report.md` 与 `fix-log.md`。
- 实际渲染后端、命令、时间和剩余风险。
