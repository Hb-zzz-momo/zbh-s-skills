# 外部来源映射

参考日期：2026-07-11。

| 仓库或文档 | 上游路径 | 参考内容 | 许可状态 | 本地采用方式 |
|---|---|---|---|---|
| Anthropic Skills / PPTX | `https://github.com/anthropics/skills/tree/main/skills/pptx` | 任务分支、文本读取、模板分析、渲染与修复复验的生产流程思想 | 专有；`skills/pptx/LICENSE.txt` 禁止复制、派生和再分发 | 仅核对流程能力边界；未复制代码、提示词、资产或文件结构，实现均为本地独立编写 |
| PptxGenJS | `https://github.com/gitbrent/PptxGenJS` | 原生 PPTX 构建 API 与包入口；核对版本 4.0.1 | MIT | 作为运行时依赖使用；本地组件和示例独立编写 |
| LibreOffice | `https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html` | headless 转 PDF 的命令行后端 | MPL/LGPL 多重许可项目 | 仅调用用户环境中已有可执行文件，不分发其二进制 |
| Poppler `pdftoppm` | `https://poppler.freedesktop.org/` | PDF 转逐页图片 | GPL-2.0-or-later | 仅调用本机工具，不分发二进制 |
| ECMA-376 OOXML | `https://ecma-international.org/publications-and-standards/standards/ecma-376/` | PPTX ZIP 包、关系文件和部件边界 | 开放标准 | 用于独立实现安全解包、打包和关系审计 |

## 许可红线

- 不把 Anthropic `skills/pptx` 的内容写入本仓库，不做改写式复制。
- 不把外部二进制打包进 Skill。
- 依赖版本、命令和许可变化时重新核对本表。

