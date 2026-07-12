# 三页纵向切片视觉 Gate（构建前契约）

代表页：S01 封面、S03 最复杂机制页、S04 示例数据页。

| 检查项 | 预期 | 构建前状态 |
|---|---|---|
| 封面 3 秒传达主张 | 标题与行动请求同时可见，右侧三张纸表达“三页” | PASS（v2） |
| 复杂页阅读方向 | 左到右 5 步，Gate 清晰，FAIL 只回到三页 | PASS（v2） |
| 数据页唯一焦点 | 两个条形对比；示例数据标签醒目 | PASS（v2） |
| 单页单结论 | 三页标题均为结论句 | 契约 PASS |
| 安全边距 | ≥ 0.42 in | PASS（边界检查 97 个元素、0 问题） |
| 最小字号 | 来源 ≥ 9 pt，正文 ≥ 14 pt | PASS（PowerPoint COM 144 DPI 人工复核） |
| 母题统一 | 朱红校样章 + 深绿结构 | 契约 PASS |
| 构图不重复 | hero / process / data-focus | 契约 PASS |
| 反 AI 模板感 | 无渐变、无发光、无同尺寸卡片墙 | 契约 PASS |
| 字体替换 | Microsoft YaHei / DengXian 回退 | PASS（PowerPoint COM 渲染层级与换行正常） |

最终 Gate：`PASS`。

- 实际后端：PowerPoint COM
- 初次证据：`vertical-slice/montage-v1.png`
- 修复后证据：`vertical-slice/montage-v2.png`
- 结构化结论：封面、机制页、示例数据页共同体现暖白纸张、深绿结构、朱红校样章；构图分别为 hero、process、data-focus，信息焦点不重复。

