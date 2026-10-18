# PPT QA 报告

- 结论：**BLOCK**
- 渲染后端：`wps-com`
- 页数：12
- 当前自动问题：9
- 前序问题：0

## 当前问题

| 严重度 | 页 | 问题 |
|---|---:|---|
| ERROR | 3 | text_boxes_overlap |
| ERROR | S02 | element_out_of_bounds |
| ERROR | S12 | element_out_of_bounds |
| ERROR | 2 | low_text_contrast |
| ERROR | 4 | low_text_contrast |
| ERROR | 6 | low_text_contrast |
| ERROR | 8 | low_text_contrast |
| ERROR | 11 | low_text_contrast |
| ERROR |  | PowerPoint COM could not open pass1; the same file was rendered by WPS for visual diagnosis. Negative-height geometry was corrected in the next build. |

## 人工视觉检查

- 审核人：未填写
- [ ] Montage 跨页节奏
- [ ] 代表页逐页检查
- [ ] 字体替换、遮挡与裁切
- [ ] 文本与图形对比度
- [ ] 图表可读性与口径

## 结论边界

自动检查不能证明不存在视觉问题；人工检查未结构化完成时结论最多为 CAUTION。
