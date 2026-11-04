# 比赛工作区蓝图

用于已经明确比赛归属、尚未确定代码技术栈的启动阶段。现有比赛根目录直接复用，不再套一层同名目录；已有清晰工程树时继续使用原工程蓝图。

```json
{
  "id": "competition-workspace",
  "classification": {
    "purpose": "competition preparation and delivery workspace",
    "deployment": "not selected at kickoff",
    "repository": "one competition workspace",
    "workflow": "understand rules, plan, implement, verify, submit",
    "stacks": []
  },
  "directories": [
    {"path": "docs", "purpose": "按用途维护赛题指南、调研、计划、设计和验收说明。", "required": true, "local_rules": ["按文档用途归位，不按调用的 Skill 建文件夹。", "原始赛题和官方材料保留在原资料目录；新增说明从根 README 链接。"]},
    {"path": "materials", "purpose": "保存官方题目、附件和来源材料；已有等价中文目录时复用并记录。", "required": false, "conditional": "with_materials"},
    {"path": "solutions", "purpose": "存放实际参赛实现或各题产品仓库，不预设语言。", "required": false, "conditional": "with_solutions"},
    {"path": "submissions", "purpose": "保存已选定版本的提交包与提交说明。", "required": false, "conditional": "with_submissions"}
  ]
}
```

最小启动只创建 `docs/` 和根入口/结构契约。指南进入 `docs/guides/`，参赛计划进入 `docs/plans/`，目录在第一次实际写入时创建。原始材料已有 `比赛资料/` 时，不开启 `with_materials` 复制同义目录，将其职责追加到实际清单。实现阶段按需要为 `solutions/` 中的产品选择自己的工程蓝图。
