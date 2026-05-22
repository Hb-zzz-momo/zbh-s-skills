---
name: artifact-curator-zh
description: "产物归档整理与过时识别技能：扫描 skill-outputs（按 skill 子目录与 legacy-flat）、实验结果、日志等；可选脚本将根目录 legacy 一键迁入 skill 子目录。Use when: skill-outputs 整理、自动按技能分文件夹、legacy 迁移、过时候选、artifact index。"
---

# 产物归档整理

## 核心原则

- **`curate_artifacts.py`**：默认**只读**扫描与整理建议，不移动、不删除、不覆盖原文件。
- **`auto_migrate_skill_outputs.py`**：在用户/项目**显式传入 `--apply`** 时，**仅**将 `skill-outputs/` 根目录下符合命名规则的 legacy 文件/夹**整件移动**到 `skill-outputs/<技能名>/`（不删文件）；不经过逐步人工确认，由调用方承担引用路径风险。干跑不加 `--apply` 或仅不传 `--apply` 时等价 `--dry-run`（只打印计划）。
- 先生成索引（或干跑迁移计划），再视需要执行 `--apply` 迁移；其它归档仍建议留痕。
- 区分“过时无用”和“历史证据”：失败复盘、红灯审计、证伪记录通常不能删，只能归入历史证据。
- 对长期科研项目，优先保护能支撑 claim、失败边界、实验口径、接班文档的文件。
- 对 `skill-outputs/`，优先做分类索引；**新产出推荐按「调用的 skill」分子文件夹**（见下文「推荐目录布局」），便于策展、交接与按技能批量归档。  
- **物理移动**仍需谨慎：移动或改名前应用全文搜索检查是否被 `AGENTS.md`、接班文档、`~/.agents/.instructions.md`、其它 `skill-outputs`、或聊天外链引用；**既有平铺旧文件**可保留为 `legacy-flat`，渐进迁移即可，不要求一次性大搬家。

## skill-outputs 推荐目录布局（按 skill 分文件夹）

基于数模等多技能协作项目的归档经验，建议**自本规范起**写入 `skill-outputs` 时采用下列结构：**目录层级以 skill 名为准，文件/文件夹名不再重复 skill 名**。

```text
skill-outputs/
├─ _curation/                    # 本技能脚本生成的只读扫描报告（保持现状）
│   └─ <timestamp>/
├─ _archive/                     # [可选] 跨 skill 的集中归档；或各 skill 下自建 _archive
├─ knowledge-digest-zh/
│   └─ 中文主题_YYYYMMDD_HHMMSS/
│       ├─ README.md
│       └─ …
├─ workflow-forge-zh/
│   └─ 工作流提炼_YYYYMMDD_HHMMSS.md
├─ research-coach-zh/
├─ project-dev-zh/
├─ paper-writing-zh/
└─ …                             # 其它 *-zh / 技能短名
```

**命名约定**

- **第一层子目录**：与技能 `name` 一致（如 `knowledge-digest-zh`），使用小写、连字符；避免与 `_curation`、`_archive` 冲突。  
- **第二层**：中文主题 + 日期时间后缀；多文件交付用文件夹 `中文主题_YYYYMMDD_HHMMSS/`，单文件用 `中文主题_YYYYMMDD_HHMMSS.md`，主题不明确时用 `结果_YYYYMMDD_HHMMSS.md`。  
- **文件名不重复 skill 名**：因为上层目录已经是 `skill-outputs/<技能名>/`，新产物不要再写 `workflow-forge-zh`、`research-coach-zh` 等前缀；只有迁移或识别旧产物时继续兼容旧规则。  
- **平铺遗留**：`skill-outputs/YYYYMMDD_HHMMSS_project-dev-zh_xxx.md` 仍合法，策展脚本将其标为 `legacy-flat`，便于索引与后续「按文件名前缀」批量迁入对应 skill 子目录。

**与其它技能的协同**

- 各写入类技能的 `SKILL.md` 已默认改为 `skill-outputs/<技能名>/`；若遇旧版 Agent 仍写到根目录，策展按 **legacy-flat** 识别即可。**策展与本索引始终以实际路径为准**。

## 快速流程

1. 确认项目根目录，优先使用当前工作区根。
2. 运行 `scripts/curate_artifacts.py` 生成只读清单（输出含 `skill_outputs_bucket` 列，区分 `legacy-flat` 与各 skill 子目录）。
3. 阅读输出目录里的四类文件：
   - `artifact_inventory.csv`
   - `stale_candidates.csv`
   - `classification_plan.csv`
   - `artifact_summary.md`
4. 只把 `stale_action=archive_candidate` 的文件列为待归档候选。
5. **仅对 `curate_artifacts.py` 的删除/移动建议**：默认需用户确认后再动手。根目录 **legacy → 按 skill 分桶** 请用下方「自动迁移脚本」单独执行，不在本步骤内自动移动。

## 自动迁移脚本（根目录 legacy-flat → `skill-outputs/<技能名>/`）

用途：把仍平铺在 `skill-outputs/` 根下的 `YYYYMMDD_HHMMSS_<技能名>-zh_…` **文件或整个文件夹**移入对应 `skill-outputs/<技能名>/`，与写入类技能默认路径一致。

规则摘要：

- 只扫描 `skill-outputs/` **直接子项**；跳过 `_curation`、`_archive`、`_auto_migrate_manifest*`、已是 `*-zh` 技能桶的目录。
- **不删除**；若目标路径已存在则跳过该条并记入 manifest。
- 默认 **干跑**（只打印）；必须加 **`--apply`** 才执行 `shutil.move`。
- 执行后生成 `skill-outputs/_auto_migrate_manifest_<时间戳>.csv`（`src,dest,status`）。

```powershell
# 干跑（默认）
python C:\Users\zbh\.agents\skills\ops\artifact-curator-zh\scripts\auto_migrate_skill_outputs.py --root "D:\path\to\project"

# 实际迁移（本项目等）
python C:\Users\zbh\.agents\skills\ops\artifact-curator-zh\scripts\auto_migrate_skill_outputs.py --root "D:\path\to\project" --apply
```

执行 `--apply` 前建议：`rg "skill-outputs/20" .` 检查是否有文档硬编码旧路径。

## 推荐命令

在项目根目录运行：

```powershell
python C:\Users\zbh\.agents\skills\ops\artifact-curator-zh\scripts\curate_artifacts.py --root .
```

指定扫描目录：

```powershell
python C:\Users\zbh\.agents\skills\ops\artifact-curator-zh\scripts\curate_artifacts.py --root D:\project\算法改进+特征选择 --dirs skill-outputs 资料\exp_start\steps 资料\exp_start\results
```

扩大到日志和结果目录：

```powershell
python C:\Users\zbh\.agents\skills\ops\artifact-curator-zh\scripts\curate_artifacts.py --root . --include-logs --include-data-step
```

## 分类标签

输出中的 `curation_class` 固定使用这些标签：

- `active-reference`：被 AGENTS、接班手册、统一认知、工作流或 Tracing 明确引用。
- `latest-topic-output`：同一主题下最新的 skill-output 或报告。
- `historical-evidence`：失败复盘、红灯审计、证伪记录、关键过程证据。
- `result-artifact`：CSV、MAT、表格、正式结果文件。
- `stale-superseded-candidate`：同主题已有更新版本，旧文件大概率只作参考。
- `temporary-or-log`：临时日志、stderr、ping、watchdog 输出。
- `unknown-review`：无法可靠判断，需要人工看标题或内容。

## 过时判断规则

把文件列为过时候选需要满足至少一种条件：

- 同主题存在更新时间更晚的文件，旧文件没有被关键文档引用。
- 文件名或内容显示该方向已失败、放弃、证伪，但它不属于必须保留的失败证据。
- 临时日志超过保留期，且不属于当前正在跑的任务。
- 重复的中间表格已被 summary 或 final 表吸收。
- 旧版本 skill-output 已被新的接班手册、统一认知或阶段总结替代。

不要把这些文件直接判为可删：

- `AGENTS.md` 引用的文件。
- `AI接班手册.md`、`项目统一认知.md`、`PlatEMO工作流细化.md`。
- `Tracing/机制注册表.md`、`Tracing/结论记录.md`、`Tracing/问题记录.md`、`Tracing/上下文压缩记录.md`。
- 红灯审计、失败复盘、证伪记录、正式结果 summary。
- 任何 `Data_step*` 中仍可能被 collector 读取的 `.mat`。

## 输出解释

`artifact_inventory.csv` 是全量索引：

- 每行一个文件。
- 包含路径、大小、修改时间、扩展名、step、版本号、主题 key、`skill_outputs_bucket`（`legacy-flat`、各 skill 子目录名、或 `_curation` / `_archive`）。

`classification_plan.csv` 是分类结果：

- 适合作为检索入口。
- 可按 `domain`、`step`、`curation_class` 筛选。

`stale_candidates.csv` 是候选清单：

- 只表示“值得检查”。
- 不表示“可以删除”。

`artifact_summary.md` 是给人看的摘要：

- 汇总各类数量。
- 列出最需要人工确认的候选。
- 给出下一步建议。

## 和项目规则的关系

在 `D:\project\算法改进+特征选择` 项目中使用时，必须遵守项目根 `AGENTS.md`：

- 不移动 `Data_step*`、`steps/stepN/`、`Tracing/` 下的正式结果，除非用户明确要求。
- 不把失败审计当垃圾文件删掉；它们通常是研究边界证据。
- 若整理导致整体工作流入口变化，需要同步更新 `PlatEMO工作流细化.md` 和 `Tracing/机制注册表.md`。
- 若只是生成索引和候选清单，不需要更新主工作流。

## 输出位置

脚本默认输出到：

```text
<project-root>/skill-outputs/_curation/<timestamp>/
```

如果项目没有 `skill-outputs/`，输出到：

```text
<project-root>/_artifact_curation/<timestamp>/
```

## 使用边界

- 这个技能负责识别、分类、生成整理计划。
- 它不负责替代科研结论判断；科研路线是否继续要用 `research-iteration-audit-zh` 或 `research-coach-zh`。
- 它不负责写论文；论文引用整理后的结果要用 `paper-writing-zh`。
