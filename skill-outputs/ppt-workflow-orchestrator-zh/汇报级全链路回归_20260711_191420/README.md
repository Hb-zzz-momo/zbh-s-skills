# 汇报级 PPT 全链路回归包

这是一套自包含回归样例，验证材料、证据、叙事、逐页契约、视觉系统、三页切片、原生 PPTX 构建、PowerPoint/WPS 双渲染、机器 QA、人工视觉复核、修复复验、模板保守编辑和最终交付。

## 最终产物

- `presentation.pptx`：10 页原生可编辑 PPTX
- `presentation.pdf`：PowerPoint 渲染 PDF
- `qa-report.md`：最终 QA 结论
- `qa/pass2/montage.png`：全量页面总览
- `workflow-state.json`：阶段门禁状态
- `delivery-manifest.json`：文件哈希与交付完整性

## 复现

在 PowerShell 中从本目录执行：

```powershell
./run-regression.ps1
```

脚本会安装本包 `src/builder` 的 Node 依赖，重新生成图表规格与 PPTX，并执行契约、构建、内容、几何、图片、图表、对比度和 Office 实际排版检查。渲染依赖本机 PowerPoint、WPS 或 LibreOffice；依赖状态见 `dependency-report.json`。

## 结论边界

CSV 是明确标注的回归示例数据，仅用于验证真实数据文件到原生图表的工程链路，不代表业务效果声明。
