# SEE / E2F + RDB WPS 复现验收记录

## 复现目标

- 视觉目标：复现参考图的三栏结构、主面板层级、红色虚线强调区、蓝/橙/灰箭头语义、Pareto 曲线、底部图例和关键标签。
- 编辑目标：WPS/PPT 原生形状可编辑，适合继续改文字、移动模块和调整箭头。
- 交付等级：L3-ish。主体由 Office 原生形状、文本框、线条、箭头和符号组成；示意曲线/散点为 Office 形状近似，不声明像素级完全一致。

## 资产来源

- 图标/符号：PPT/WPS 原生圆、三角、菱形、星形、矩形、箭头、线条；无 `API`、`DB`、`USR` 等字母占位冒充图标。
- 字体：Arial。
- 数据/标签：来自用户提供参考图可见文本；曲线和散点为示意复现，不代表真实实验数据。

## 目标软件验收

- WPS MCP 打开：PASS。`see_e2f_rdb_wps_reproduction_final.pptx` 已通过 `wps_ppt_open_presentation` 打开。
- WPS MCP 导出：PASS。已通过 `wps_convert_format` 导出 PNG。
- WPS 导出图尺寸：PASS。`2304 x 1296`，16:9。
- 可编辑性：PASS with boundary。`pptx_structure_audit.json` 显示 1 页幻灯片、0 个嵌入媒体文件，主体不是固定背景图。

## 严格审计结果

- 文本布局审计：PASS。`text_layout_audit.json` 中 `total_text_items = 113`，`caution_count = 0`。
- 全图裁剪审计：PASS。已生成 9 个 WPS 渲染裁剪区和 contact sheet。
- 图例裁切：PASS。最终版已修正底部图例越界问题。
- 箭头压字：PASS。最终版已修正左侧 Step 5 到初始种群的箭头压住 `bandMaxRatio` 的问题。
- 重复结构检查：PASS。左侧步骤卡片、中部 offspring 三 lane、评估/归档/前沿区、右侧输出区、底部图例均单独裁剪检查。

## 交付文件

- WPS/PPT 可编辑源文件：`see_e2f_rdb_wps_reproduction_final.pptx`
- WPS 导出 PNG：`see_e2f_rdb_wps_render.png`
- 原始 WPS 导出目录：`wps_export_final/幻灯片1.png`
- 文本审计：`text_layout_audit.json`
- PPTX 结构审计：`audits/pptx_structure_audit.json`
- WPS 渲染审计：`audits/wps_visual_audit.json`
- 裁剪 contact sheet：`audits/wps_render_contact_sheet.png`
- 生成脚本：`render_see_e2f_rdb_wps_reproduction.py`
- 审计脚本：`make_wps_audit_crops.py`

## 残余风险

- 参考图中极小 OCR 文本存在少量不可辨识处，已按可见语义复现，未额外发明不可确认内容。
- 该版本是科研机制/流程图复现，不是从论文原始矢量文件反向还原；因此不声明像素级完全一致。

## 放行状态

PASS：满足本轮“WPS MCP 复现 + 严格验收”要求，可作为 WPS 可编辑演示源文件和 PNG 展示图继续使用。
