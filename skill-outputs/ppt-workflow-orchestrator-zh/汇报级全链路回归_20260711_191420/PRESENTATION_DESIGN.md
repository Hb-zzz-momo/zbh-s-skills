# PRESENTATION_DESIGN

## Design Read

温暖纸张底色承载工程严谨感；朱红负责结论和行动，墨绿负责流程与验证。唯一视觉母题是“左侧轨道 + 闭环曲线”，避免常见蓝紫渐变科技模板。

## Rules

- 16:9，安全边距 0.55 in，基准间距 0.28 in。
- 标题 24 pt，正文 15 pt，关键数字 28 pt；每页只保留一个结论。
- 页面节奏按“留白开场 → 双栏对比 → 矢量机制 → 数据高峰 → 表格复核 → 图片呼吸 → 流程收束”变化。
- 禁止连续三页标题加项目符号、无意义三列卡片、整页截图、装饰性 3D 图表。

```presentation-theme
{
  "slide": {"width": 13.333, "height": 7.5, "margin": 0.55},
  "colors": {"ink": "172033", "muted": "5E6B7A", "paper": "F7F4ED", "surface": "FFFFFF", "accent": "E05A47", "accent2": "146A65", "line": "D7D9DD"},
  "fonts": {"head": "Microsoft YaHei", "body": "Microsoft YaHei", "mono": "Consolas"},
  "sizes": {"hero": 30, "title": 24, "body": 15, "small": 10, "metric": 28},
  "radius": 0.12,
  "gap": 0.28,
  "layout_families": ["hero", "split", "process", "comparison", "chart-native", "table", "visual-image"],
  "motif": "左侧朱红轨道与墨绿闭环曲线",
  "forbidden_patterns": ["连续三页标题加项目符号", "无意义三列卡片", "整页截图", "3D图表"]
}
```
