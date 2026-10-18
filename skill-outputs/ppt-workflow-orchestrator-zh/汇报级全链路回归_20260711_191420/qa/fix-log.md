# 修复记录

## Pass 1 发现的问题

1. `check_geometry.py` 把母版页码占位符当成正文框，与来源脚注产生 10 个同构重叠误报。
2. `check_image_resolution.py` 把 SVG 的 PNG 兼容预览当作位图计算 PPI，产生 12.5 PPI 误报。
3. `check_contrast.py` 对 `NoFill` 直接访问前景色而崩溃。
4. `check_office_layout.py` 的单行条件语句导致成功分支未初始化 `allowed`。
5. S02 的 16 pt 墨绿文字在纸色背景上的对比度为 4.39，低于普通正文 4.5 的门禁。

## 根因修复

- 几何检查显式排除 `Slide Number Placeholder`，保留正文之间的重叠检查。
- 图片检查按构建器对象名识别 `-svg` 矢量对象，记录为 vector，不计算无意义 PPI。
- 对比度检查仅在 `SOLID` 填充时读取前景色，其余使用显式页面背景色。
- Office 检查拆分条件分支与结果解析，确保成功路径初始化变量。
- 将视觉令牌 `accent2` 从 `#1B7F79` 加深为 `#146A65`；在纸色背景上的对比度提升到 5.83，同时保持原有墨绿语义。

## 复验要求

- 对同一 Pass 1 PPTX 重新运行四个检查器，证明检查器根因已修复。
- 从同一 `slide-spec.json` 重新构建 Pass 2，使用 PowerPoint 与 WPS 双渲染。
- Pass 2 完成机器检查和结构化人工视觉复核后，才允许生成最终 `qa-report.md`。
