# 产物分类策略

## skill-outputs：按 skill 分子文件夹（推荐）

与「根目录平铺 `YYYYMMDD_*_skill-zh_主题.md`」以及「skill 子目录里继续重复 skill 名」相比，推荐新产出写入：

```text
skill-outputs/<skill-name>/中文主题_YYYYMMDD_HHMMSS/
```

或单文件：

```text
skill-outputs/<skill-name>/中文主题_YYYYMMDD_HHMMSS.md
```

新产物命名规则：主题在前，日期时间在后；主题优先使用可读中文短语，主题不明确时使用 `结果_YYYYMMDD_HHMMSS`。因为路径中已有 `<skill-name>`，文件/文件夹名不要再重复 skill 名。

**策展脚本**会将 `skill-outputs/` 下第二层符合 `YYYYMMDD_HHMMSS_*` 的旧条目标为 `legacy-flat`；将 `knowledge-digest-zh` 等技能名目录标为该 skill 的 `skill_outputs_bucket`，便于按技能筛选与批量迁入 `_archive`。

迁移平铺旧文件时：优先按**文件名中的技能前缀**（与 `curate_artifacts.py` 中 `SKILL_PREFIX_RE` 一致）归入对应 `<skill-name>/`，迁完更新引用路径。

## 推荐目录视图

不要一上来物理移动文件。优先生成检索视图：

```text
skill-outputs/_curation/<timestamp>/
├─ artifact_inventory.csv
├─ classification_plan.csv
├─ stale_candidates.csv
└─ artifact_summary.md
```

如果后续用户确认要整理，可以采用二级归档：

```text
skill-outputs/_archive/
├─ active-reference/
├─ historical-evidence/
├─ stale-superseded/
├─ temporary-logs/
└─ unknown-review/
```

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
