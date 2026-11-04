# 产物分类策略

## 按项目用途归位

新文档遵从[项目文档路由](../../../engineering/project-structure-architect/references/document-routing.md)。项目根、真实主题和用途决定位置；作者是 AI 或调用了某个 Skill 都不产生独立桶。持续维护文档用稳定主题名；事件报告与冻结版本按日期或版本留存。

新盘点清单进入项目评审/报告目录，默认 `docs/reviews/artifact-curation/<timestamp>/`；已有 `reports/` 时复用其下的 artifact-curation。用 `--output` 传入项目特有位置。

旧 `skill-outputs/` 的 legacy-flat 和技能桶仍用于历史分类；不把历史兼容规则当作新目录建议。旧桶迁移先按实际内容与现行版建立映射，确认引用，不用整个 Skill 桶代替业务归类。

## 主题 key 规则

主题 key 用来判断同主题旧文件是否被新文件覆盖。

规则：

- 去掉时间戳，包括旧式前缀 `20260507_160822_` 和新式后缀 `_20260507_160822`。
- 去掉常见技能名前缀，如 `research-coach-zh`、`research-iteration-audit-zh`。
- 保留 step、算法分支、任务关键词，如 `step83_skeleton_identity`。
- 同一主题下修改时间最新的文件优先标为 `latest-topic-output`。

**按 skill 子目录布局时的补充**（由脚本 `delivery_topic_key` 实现）：

- 若路径为 `skill-outputs/<skill>/<run_folder>/...`，则以 **`<skill>/<run_folder>`**（去掉 `run_folder` 的旧式时间戳前缀或新式时间戳后缀后）作为同一「交付批次」的 topic key，避免把同一次交付里的 `README.md` 与 `知识总结.md` 拆成多个无关主题。
- 平铺 `legacy-flat` 仍仅按文件名规则抽取 topic key。

## 失败文件的处理

失败文件不是垃圾。

以下内容应标记为 `historical-evidence`：

- `失败复盘`
- `红灯`
- `证伪`
- `hard stop`
- `stop`
- `不再继续`
- `待突破问题`

只有当失败文件已被更高层总结吸收，并且没有被关键文档引用时，才可列为 `archive_candidate`。

## 结果文件的处理

`.csv`、`.mat`、`.xlsx` 等结果文件按来源判断：

- `steps/stepN/` 下：通常保留在原位。
- `results/` 下：阶段冻结结果，不应随意移动。
- `Data_step*` 下：正式运行结果，不应移动或删除。
- 临时日志和 stderr：可以进入过时候选。

## 删除门槛

任何文件要删除前必须满足：

- 不在关键文档引用列表中。
- 不是正式结果或失败证据。
- 有明确更新版本或最终 summary 替代。
- 用户明确确认。
