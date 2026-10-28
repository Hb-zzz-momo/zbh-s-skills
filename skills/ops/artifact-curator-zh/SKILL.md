---
name: artifact-curator-zh
description: "产物归档与任务收尾清理：识别重复/过时产物，验收后按精确清单清理本轮临时文件和已核验副本，保留最终交付、复现依赖及关键证据。用于实验结束磁盘瘦身、版本过多、产物索引及 skill-outputs 迁移；不作全盘垃圾清理。"
---

# 产物归档整理

若用户要在整个项目或活动结束后整理沉淀，以用户技能 `project-closeout-zh` 为主线，按真实业务主题、用途和内容版本实际归位；不能整桶搬outputs/skill-outputs后只写导航。本技能只补盘点、重复候选和验收后的受限清理；扫描完整不等于内容好找。
<!-- project-structure-architect:gate:v1:start -->
## Project structure gate / 文件树结构门禁

只要本工作流将初始化或重组项目，或新建、移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树，必须先使用 `project-structure-architect`。

1. 开始前：读取适用的 `AGENTS.md`、`PROJECT_STRUCTURE.md`、`.project-structure.yaml` 和现有文件树，锁定项目类型、蓝图及唯一合理路径。
2. 运行中：每次新增或移动文件前先判断职责、所有者、复用范围和对应测试；禁止同义目录、根目录堆放、跨层混放及无关重组。
3. 阶段收口：纵向切片或阶段完成后检查结构漂移；新项目或重大重组更新结构文档，最终运行结构审计。出现 `BLOCK` 时停止结构性写入并先修正或询问用户。

纯内容编辑且目标路径已由用户或现有规范唯一确定时，可不重复调用。
<!-- project-structure-architect:gate:v1:end -->

## 核心原则

- **`curate_artifacts.py`**：默认**只读**扫描与整理建议，不移动、不删除、不覆盖原文件。
- **`auto_migrate_skill_outputs.py`**：在用户/项目**显式传入 `--apply`** 时，**仅**将 `skill-outputs/` 根目录下符合命名规则的 legacy 文件/夹**整件移动**到 `skill-outputs/<技能名>/`（不删文件）；不经过逐步人工确认，由调用方承担引用路径风险。干跑不加 `--apply` 或仅不传 `--apply` 时等价 `--dry-run`（只打印计划）。
- 先生成索引（或干跑迁移计划），再视需要执行 `--apply` 迁移；其它归档仍建议留痕。
- 区分“过时无用”和“历史证据”：失败复盘、红灯审计、证伪记录通常不能删，只能归入历史证据。
- 对长期科研项目，优先保护能支撑 claim、失败边界、实验口径、接班文档的文件。
- 所有新文档按项目和用途归位；`skill-outputs/` 仅作历史扫描输入，不再推荐按 Skill 分桶。
- **物理移动**仍需谨慎：移动或改名前应用全文搜索检查是否被 `AGENTS.md`、接班文档、`~/.agents/.instructions.md`、其它 `skill-outputs`、或聊天外链引用；**既有平铺旧文件**可保留为 `legacy-flat`，渐进迁移即可，不要求一次性大搬家。

## 项目用途目录与历史兼容

新文档依 `project-structure-architect` 的[用途路由](../../engineering/project-structure-architect/references/document-routing.md)进入所属项目。盘点报告写入项目评审/报告目录；已有中文目录或契约映射时通过 `--output` 指定，不创建同义目录。

```text
<project>/
  docs/guides/             # 入门和操作说明
  docs/research/           # 资料调研
  docs/plans/              # 当前计划
  docs/reviews/            # 盘点、审计与验收；已有 reports/ 时可复用
  比赛资料/               # 已有官方材料目录，保留原件
```

历史平铺与技能桶仍能由 `skill_outputs_bucket` 识别，但这只是索引字段，不决定新存放位置。迁移前阅读内容、判定用途和现行版、检查引用，再执行获准范围内的精确移动；不能只按原 Skill 整桶归档。

## 快速流程

1. 确认项目根目录，优先使用当前工作区根。
2. 运行 `scripts/curate_artifacts.py` 生成只读清单（输出含 `skill_outputs_bucket` 列，区分 `legacy-flat` 与各 skill 子目录）。
3. 阅读输出目录里的四类文件：
   - `artifact_inventory.csv`
   - `stale_candidates.csv`
   - `classification_plan.csv`
   - `artifact_summary.md`
4. 只把 `stale_action=archive_candidate` 的文件列为待归档候选。
5. 未获准的删除/移动建议先确认范围；已授权的项目整理按精确内容映射执行。不要默认调用旧布局迁移工具。

## 验收后的收尾清理

用户已要求把实验结束清理纳入工作流时，执行[最小留存与清理](references/experiment-closeout.md)。只读扫描候选不是删除授权；本轮已获准的、能证明无用的临时文件和重复副本无需逐项再问，判断不明的保留并说明。不从“旧版本”“失败”“没有被全文搜索命中”推断可删。

- 开始时记录本任务创建的临时目录和子进程；数据、共享模型和源码保持单一权威来源，不为每轮评审复制完整目录。
- 结束时先冻结最终交付与复现/证据保留集合，确认实际验收完成、没有运行中的消费者，再生成精确文件清单。
- 用 `scripts/closeout_artifacts.py --plan <plan.json>` 只读预检；同一已授权范围用 `--apply --journal <cleanup.jsonl>` 执行。任一候选不安全时预检整体拒绝；不直接把 `stale_candidates.csv` 喂给删除命令。
- 执行器只逐文件删除当前任务拥有范围内、指纹未变的重建缓存/视图或与保留者逐字节一致的副本；不递归删除目录，不清全局环境/共享缓存，不调用云端清理API。云盘同步目录中的本地删除可能同步到云端，须按实际项目留存范围处理；不能把它说成只释放本机缓存。计划、验收记录、保留者和审计日志受保护。
- 磁盘与内存分别收口：清理文件只报告实际删除及逻辑字节；内存靠关闭本任务内核、模型进程与临时浏览器释放，不能杀其他聊天或用户应用，也不能承诺删文件就释放RAM。
- 用一份小清单记录删除理由、保留者/重建入口、SHA256、实际结果及仍不确定项；不要为清理再制造一套全量备份、多版ZIP或测试输出树。

## 旧布局迁移工具（仅明确要求旧布局时）

用途：把仍平铺在 `skill-outputs/` 根下的 `YYYYMMDD_HHMMSS_<技能名>-zh_…` **文件或整个文件夹**移入对应 `skill-outputs/<技能名>/`，仅供用户明确要求保留旧技能桶布局时兼容使用，不是新项目规范，也不能代替内容归位。

规则摘要：

- 只扫描 `skill-outputs/` **直接子项**；跳过 `_curation`、`_archive`、`_auto_migrate_manifest*`、已是 `*-zh` 技能桶的目录。
- **不删除**；若目标路径已存在则跳过该条并记入 manifest。
- 默认 **干跑**（只打印）；必须加 **`--apply`** 才执行 `shutil.move`。
- 清单默认复用已有 reports 或文档评审目录，写入其 `artifact-migration/`；`--output <目录>` 可明确指定项目位置（相对路径以项目根解析），文件名为 `_auto_migrate_manifest_<时间戳>.csv`。干跑不写清单。

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

有既定项目评审目录时以 `--output` 传入；默认复用已有 `reports/artifact-curation/<timestamp>/`，否则使用已有文档根下的 `reviews/artifact-curation/<timestamp>/`，没有文档根时使用 `docs/`。多个文档根并存时明确传入目标，不默选。无论是否已有旧 skill-outputs，新盘点清单都不写回旧桶。

默认扫描覆盖项目 docs、文档、reports、paper、materials、references、比赛资料及旧 skill-outputs；自定义职责目录用 `--dirs` 补充。跳过历次 artifact-curation 清单，避免自我索引。索引只盘点，不移动源文件。

## 使用边界

- 这个技能负责识别、分类、生成整理计划，并在已授权且验收完成的任务内执行上述受限清理。
- 它不负责替代科研结论判断；科研路线是否继续要用 `research-iteration-audit-zh` 或 `research-coach-zh`。
- 它不负责写论文；论文引用整理后的结果要用 `paper-writing-zh`。
