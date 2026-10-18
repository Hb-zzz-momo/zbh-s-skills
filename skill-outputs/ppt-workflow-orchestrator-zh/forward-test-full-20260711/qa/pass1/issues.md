# Pass1 问题记录

| Issue ID | Slide | 严重度 | 证据 | 源文件 | 修复 | 复验 |
|---|---|---|---|---|---|---|
| QA-001 | S04 | ERROR | `geometry.json`：校样章边框与文字为两个完全重叠对象 | `src/components.ts` | 合并为单一带边框文本框 | PASS：最终 geometry 167 shapes、0 issues |
| QA-002 | S04 | ERROR | `charts.json`：native_chart_count 0 < 1 | `src/build.ts` | 以 PowerPoint 原生条形图替代手工条形 | PASS：1 chart / 1 series / 2 categories |
| QA-003 | 多页 | ERROR | 对比度检查发现朱红/灰色令牌在真实背景下不足 | `src/theme.ts`、`PRESENTATION_DESIGN.md` | 朱红改为 A93624，灰改为 56625C；深绿页章用浅桃色 | PASS：125 runs、0 issues |
| QA-004 | S04 | ERROR | 中间版出现原生图表与旧手工条形重复 | `src/build.ts` | 删除旧轴、刻度、条形与标签，仅保留原生 Chart | PASS：最终 Montage 无重复 |
| QA-005 | S04 | ERROR | 中间版示例边界文本框侵入标题框 | `src/build.ts` | 将边界标注下移至 y=1.66 | PASS：最终 geometry 0 issues |
| QA-006 | S02 | WARNING | “最昂贵”超出现有证据强度 | `slide-spec.json`、`src/build.ts` | 收敛为“三类关键的方向性错误” | PASS：契约复验 0 issues |

