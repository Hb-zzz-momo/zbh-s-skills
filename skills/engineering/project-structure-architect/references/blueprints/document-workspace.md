# 文档先行项目蓝图

用于明确归属于一个项目、当前只需要资料与文档且确需脚手架的阶段。普通小文档可直接复用现有主题和 README，不强制生成此蓝图或 manifest；已有产品工程延续其蓝图。

```json
{
  "id": "document-workspace",
  "classification": {
    "purpose": "documentation-first project workspace",
    "deployment": "not applicable at current stage",
    "repository": "single project workspace",
    "workflow": "research, explain, plan, and deliver documents",
    "stacks": []
  },
  "directories": [
    {"path": "docs", "purpose": "保存本项目按用途分类的说明、计划和正式文档。", "required": true, "local_rules": ["在首次生成文档前确定项目归属与用途，不创建 skill-output(s) 目录。", "维护根 README 的实际阅读链接；仅创建本次需要的文档子目录。"]},
    {"path": "references", "purpose": "保存外部原始来源与参考附件，区别于项目生成说明。", "required": false, "conditional": "with_references"}
  ]
}
```

用户已给项目根时直接使用它；处于多个项目的共同父目录且归属无法判断时，先明确项目，不能自行新建“结果”或“AI文档”收纳桶。`docs` 是此工程脚手架的默认职责名，不要求把普通资料移入它。普通资料按[主题、用途与版本](../document-versions.md)组织；已有中文目录继续沿用，已有 manifest 时通过 `document_routes` 记录适用映射。
