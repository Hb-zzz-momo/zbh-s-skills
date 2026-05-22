# artifact-curator-zh 迭代日志

## 2026-05-11 迭代 #3

- **触发反馈**：用户希望**不经逐步人工确认**，将 `skill-outputs` 根目录 legacy 直接迁入按技能分子目录，并在本项目执行。
- **修改内容**：新增 `scripts/auto_migrate_skill_outputs.py`（默认干跑；`--apply` 执行移动；可选 `--no-rewrite-md`）；`SKILL.md` 区分 `curate_artifacts.py`（只读）与本脚本（显式 `--apply` 才移动）；迁移后默认批量替换仓库内 `*.md` 中的旧相对路径；已在 `2026数维杯` 仓库执行 `--apply` 生成 `_auto_migrate_manifest_*.csv`。
- **影响范围**：策展技能交付物；其它项目需自行承担引用风险后执行。

## 2026-05-11 迭代 #2

- **触发反馈**：用户要求 `knowledge-digest-zh`、`workflow-forge-zh` 等与 `artifact-curator-zh` 策展规范对齐，默认写入 `skill-outputs/<技能名>/`。
- **修改内容**：已同步更新 `~/.agents/skills/` 下多个写入类技能 `SKILL.md` 的默认路径与「最终回复须含前缀」条款；本技能「与其它技能的协同」段落改为反映已落地状态。
- **影响范围**：仅文档约定；不自动迁移仓库内既有平铺文件。

## 2026-05-11 迭代 #1

- **触发反馈**：用户基于数模项目归档经验，希望 `skill-outputs` 今后可按**调用的 skills** 分子文件夹，便于整理与检索。
- **根因**：原技能强调「不要轻易物理移动」但未给出**可扩展的目录约定**；策展脚本缺少 `skill_outputs_bucket`，难以按技能维度统计或规划迁移。
- **修改内容**：
  - `SKILL.md`：新增「推荐目录布局」、命名约定、与平铺 `legacy-flat` 共存及迁移前引用检查；更新核心原则与 `artifact_inventory` 字段说明。
  - `references/classification-policy.md`：补充按 skill 子目录的推荐树、`topic_key` 与脚本 `delivery_topic_key` 对齐说明。
  - `scripts/curate_artifacts.py`：新增 `skill_outputs_bucket`、`delivery_topic_key`；CSV 增加 `skill_outputs_bucket` 列；`artifact_summary.md` 增加 bucket 计数段。
- **影响范围**：扫描与 stale 判定逻辑（同 skill 子目录内多文件共享 `topic_key`）；不改变默认「只读、不自动移动」边界。
