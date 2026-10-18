# 要求覆盖矩阵

| ID | 要求 | 实现 | 测试 | 交付证据 | 当前状态 |
|---|---|---|---|---|---|
| R01 | 6 页 | `slide-spec.json` 与构建脚本固定 6 页 | 读取 PPTX 页数、PDF 页数、PNG 数量 | `presentation.pptx`、`qa/` | 进行中 |
| R02 | 16:9 | 构建脚本使用宽屏页面 | 读取 PPTX 页面尺寸 | QA 报告 | 进行中 |
| R03 | 中文 | 全部页面与备注使用中文 | 文本抽取检查 | `qa/text-extract.txt` | 进行中 |
| R04 | 原生可编辑 | 文字、线条、图表、标识均用原生对象 | PPTX XML/对象统计 | `qa/editability-audit.json` | 进行中 |
| R05 | 视觉精致且符合暖白+深绿+朱红编辑部风格 | 建立设计令牌、网格、母题与版式家族 | 三页切片审美 Gate + 全量 Montage 人工 QA | `PRESENTATION_DESIGN.md`、QA 报告 | 进行中 |
| R06 | 三页纵向切片 | 先构建封面、机制页、示例数据页 | 切片 PPTX 实际渲染与记录批准 | `vertical-slice/` | 进行中 |
| R07 | 全量构建 | 切片通过后构建 6 页 | 重新构建与打开导出 | `presentation.pptx` | 进行中 |
| R08 | PowerPoint 或 WPS 实际渲染 | 使用本机真实 Office 后端导出 PDF | PDF 页数与逐页图片 | `qa/render-engine.txt`、`qa/slides/` | 进行中 |
| R09 | 至少一轮问题记录、修复、复验 | 首轮渲染后形成问题清单，修改源代码并重建重渲染 | 对比首轮/复验结果 | `qa/fix-log.md`、`qa/qa-report.md` | 进行中 |
| R10 | 结构化人工 QA | 内容、几何、图片、视觉、来源、节奏逐项检查 | 人工逐页记录 + 自动检查辅助 | `qa/structured-human-qa.md` | 进行中 |
| R11 | 示例数据边界 | 数据页醒目标注“示例数据”并在备注说明 | 文本扫描检查每个数字主张的标签 | `sources.md`、`claim-evidence-map.md` | 进行中 |
| R12 | 仅写指定目录 | 所有新文件集中到目标目录 | Git/文件系统路径审计 | `self-derivation-audit.md` | 进行中 |
| R13 | 不修改 Skill 源文件 | 只读使用 Skills | Git diff/mtime 范围审计 | `self-derivation-audit.md` | 进行中 |
| R14 | 报告实际产物、命令、QA 结论、工作流缺陷 | 形成 README/报告并向父代理回报 | 交付清单完整性校验 | `README.md`、最终回报 | 进行中 |

