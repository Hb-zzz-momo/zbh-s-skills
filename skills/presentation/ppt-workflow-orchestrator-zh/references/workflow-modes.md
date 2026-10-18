# PPT 工作流模式与路由

| 模式 | 判定 | 阶段主 Skill | 必要验收 |
|---|---|---|---|
| A 仅规划 | 只要大纲、页面结构、故事线或演讲顺序 | `ppt-story-design-zh` | 主张—证据映射与逐页契约自检 |
| B 从零创建 | 无可复用模板，要求可编辑 PPTX | `pptx-builder-zh` | `ppt-render-qa-zh` 完整复验 |
| C 基于模板 | 用户提供模板并要填充新内容 | `pptx-template-editor-zh` | 模板映射后完整复验 |
| D 修改已有 | 增删、替换或调整现有 PPTX | `pptx-template-editor-zh` | 受影响页回归与全局 Montage |
| E 数据增强 | 含科研、建模、经营或统计数据 | 当前 B/C/D 主 Skill | 数据页阶段追加 `ppt-data-storytelling-zh` |

## 最小加载示例

```text
阶段：Narrative
主：ppt-story-design-zh
辅：info-evidence-chain-zh
完成后卸载：info-evidence-chain-zh
```

```text
阶段：Build（从零）
主：pptx-builder-zh
辅：ppt-visual-system-zh
验收阶段切换主 Skill：ppt-render-qa-zh
```

不得把总控、叙事、视觉、构建、模板编辑、数据和 QA 同时加载。

## 模式 D 强制顺序

1. 复制原文件并记录 SHA-256。
2. 分析页面结构、主题、母版、字体、动画和关系文件。
3. 生成页面映射与变更清单。
4. 保守修改，另存为新文件。
5. 渲染受影响页并执行全局回归。

