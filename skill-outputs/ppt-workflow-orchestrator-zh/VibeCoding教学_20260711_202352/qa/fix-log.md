# PPT 修复复验记录

| issue_id | slide_id | severity | evidence | source_file | fix | retest_result |
|---|---|---|---|---|---|---|
| FULL-001 | S02、S12 | ERROR | `build-check` 检出角箭头使用负高度，元素盒越界 | `src/build.ts` | 将两条斜线改为正高度坐标表达 | 最终边界检查 PASS |
| FULL-002 | S03 | ERROR | `check_geometry` 检出定义主张与蓝色强调词文本框重叠 | `src/build.ts` | 将 `different` 下移，分离文本边界 | 最终几何检查 PASS |
| FULL-003 | S02、S04、S06、S08、S11 | ERROR | 蓝底页脚文字对比度 4.17，低于 4.5 | `src/components.ts` | 深色页脚色从 `C8CDD2` 提亮为 `EAF0F7` | 最终对比度检查 PASS |
| FULL-004 | S05 | ERROR | PowerPoint 实测三个大号编号文字高度 57.6pt，高于 54.72pt 容器 | `src/build.ts` | 编号文本框高度由 0.76in 增至 0.90in | 最终 Office 布局检查 PASS |
| FULL-005 | S07 | ERROR | PowerPoint 实测提示结论宽度超出容器约 1pt | `src/build.ts` | 文本框宽度由 3.24in 增至 3.55in | 最终 Office 布局检查 PASS |
| FULL-006 | 全套 | WARNING | pass1 PowerPoint COM 首次打开报文件不可读；同一文件可由 WPS 打开 | `src/build.ts` | 修复负高度几何后重新构建 | 后续两轮均由 PowerPoint 与 WPS 成功渲染 |

最终结论：前序阻断项全部消除，PowerPoint/WPS 双后端复验通过。
