# Slide Contract 结构

`slide-spec.json` 顶层必须包含 `deck` 与 `slides`。每页必填：

```json
{
  "slide_id": "S06",
  "section": "核心方案",
  "purpose": "解释输入到结果的执行闭环",
  "audience_takeaway": "方案是可验证闭环",
  "claim": "渲染与修复是可靠交付的必要组成",
  "evidence_refs": ["SRC-003"],
  "visual_type": "circular_process",
  "layout_family": "center-diagram-with-side-annotations",
  "dominant_asset": "agent-loop.svg",
  "content_blocks": [{"type": "process_node", "content": "PLAN"}],
  "text_budget": {"title": 18, "body": 55, "footer": 20},
  "source_footer": ["SRC-003"],
  "speaker_notes": "先讲一次生成，再讲闭环差异。",
  "qa_checks": ["流程方向清晰", "文字无溢出", "引用可追溯"]
}
```

## 校验规则

- `slide_id` 在整套 Deck 内唯一，按演讲顺序排列。
- `claim` 只含一个主要结论；章节名不能替代结论标题。
- 每个 `evidence_refs` 必须能在 `sources.md` 中解析。
- `content_blocks` 只放页面需要表达的内容，不放版式坐标。
- `text_budget` 计汉字、英文单词和数字，不以字符宽度冒充视觉验收。
- `source_footer` 只列本页真正使用的来源。
- `qa_checks` 至少覆盖内容、几何与来源三类。

