# 实验收尾：最小留存与清理

适用于用户要求结束后清理的课程/科研任务。先做出并验收用户要的产物，再收尾；不把“整理”变成删除原始材料或扩大提交范围。本流程不授予全盘、共享缓存或云端服务清理权限。WPS/OneDrive等同步目录的本地删除可能被客户端同步到云端；按实际项目授权与保留集合处理，不能声称仅释放本机缓存。若用户只要求释放本地占用而保留云端原件，应另查客户端的释放本地空间功能，不用unlink冒充。

## 先少产生，再清理

- 沿用现有项目目录。开工登记本轮独占的 scratch/解压验证目录、子进程、应保留文件与可重建输出；未知归属不补猜。
- 同一数据、源码和共享模型只保留一个权威来源。相同版本的评审冻结用路径+SHA256索引，不复制整套数据、模型、ZIP与Notebook；图像未变的页面复用已有实际视觉结论。
- 解压重跑需要独立目录时，验证后只回收该独占目录里的冗余副本。临时文件用上下文管理器/`finally`回收，先取回必须留存的原生结果及诊断。
- “保留每轮记录”指配置/变更、指标、真实诊断与必要证据，不意味着每轮都留完整环境、模型目录和压缩包。训练checkpoint按实验需要保存best、必要的resume或轨迹；不默认每epoch另存一大份。

## 留存集合

| 对象 | 默认处理 |
|---|---|
| 当前用户指定的最终提交文件、对应CSV/报告、必要披露 | 每个课程/身份/目标保留一个当前正式命名；ZIP成员严格按当前提交要求，不塞入额外模型/数据/QA记录 |
| 复现所需源码、参数/种子、环境清单、数据及选中模型的依赖闭包 | 保留单一可查来源；没有验证替代来源就不能删唯一数据/模型。提交包只含IPYNB+HTML时，复现依赖留在项目内部 |
| 原始题目/模板、原始采集截图、关键失败日志、解释对比结果所需的raw/summary、评审原始意见及作者处理 | 保护；不能用一段摘要、哈希或“已有新版本”代替唯一证据 |
| 拷贝到临时解压目录的同字节数据/模型/代码、同字节候选ZIP和过时备份 | 有仍保留的同字节来源、引用已处理、消费者结束后可清理；最终交付链接指向的文件不能删 |
| 本轮缓存、临时下载片段、可重建的打印页PNG/蒙太奇 | 先保留最终PDF/HTML、生成入口和必要审核依据，再列精确候选；唯一实验截图不是“生成视图” |
| 非重复的旧模型/结果、未知文件、待排错现场、其他任务文件、运行中消费者的输入 | 不自动删；领域判断尚未完成时列为保留，不能按日期、大小、`old/tmp/fail`文件名直接判定 |

已经冻结/签章的证据路径不能悄悄消失。计划清理被索引的**副本**时，先验证保留者SHA并补一条旧路径→保留者的重定位索引，不改写历史事实；唯一证据留原件。未能建立可查替代路径时保留。清理后原路径不再存在，就不能继续宣称旧seal或目录级检查仍全部可解析。

## 收尾动作

1. 确认用户提交要求和实际终态：最终文件可打开、必做检查与必要复现已通过，所需原生输出已保存。未通过时先保存必要故障现场，不以清理覆盖错误。
2. 由领域执行者标记依赖/证据保留集合和消费者关系；脚本不会自动推导`protected`或依赖闭包，Notebook/collector动态依赖和最终交付链接必须由执行者纳入。查询引用是辅助检查，不等于已证明全部引用已找到。
3. 关闭**本轮拥有**的内核、模型子进程、监控器与临时浏览器；核对PID、命令行/任务标识和真实退出，防止PID复用误杀。不要结束其他聊天的MCP服务、用户虚拟机或应用。失败/取消也要在允许范围内关闭本轮资源。
4. 生成下面的精确计划并dry-run。当前用户指令或已适用的持续授权覆盖这些明确的本轮临时/重复文件时，直接apply，不因旧“建议需确认”重复询问。未知项只保留说明，不阻断其它安全项；把它们排除出本次计划。
5. 删除后检查保留集合与正式产物hash不变、依赖/索引可解析，记录实际删除清单。只有清理改变运行依赖、代码或证据解释时才重跑受影响检查；不为文件瘦身反复做全量训练或再造验收副本。

## 精确清单执行器

`scripts/closeout_artifacts.py`只消费已经审定的计划，不从扫描标签自动推断“无用”，不运行`generator`字符串、不关闭进程。默认dry-run不创建日志；apply必须有独占新建的JSONL日志。对已经停用的任务由调用者如实设置`workers_stopped`，这个字段不是进程自动检测。

计划示例（SHA256和size须从真实文件计算，示例不是可直接执行的删除授权）：

```json
{
  "root": "D:/project/lab",
  "owned_roots": ["evidence/run-001/scratch"],
  "protected": ["data", "models", "src", "report.ipynb", "report.html", "final.zip", "evidence/retained"],
  "validation": {"path": "evidence/acceptance.json", "sha256": "actual_sha256"},
  "workers_stopped": true,
  "items": [
    {"path": "evidence/run-001/scratch/train.csv", "size": 123, "sha256": "actual_sha256", "reason": "duplicate", "keeper": "data/train.csv"},
    {"path": "evidence/run-001/scratch/page-001.png", "size": 456, "sha256": "actual_sha256", "reason": "temporary", "generator": "render retained report.html; reviewed PDF retained"}
  ]
}
```

`protected`只填实际存在的路径；所有路径在实验根内，验收记录须为hash匹配的JSON，状态为`PASS`或`PASS_WITH_NONBLOCKING_CAUTIONS`。原计划、验收记录、日志、保留者均不能被删。重复文件的保留者必须不在删除集合，大小和内容SHA都相同；同名、旧日期或数值近似不能替代逐字节验证。

```text
python <skill>/scripts/closeout_artifacts.py --plan <experiment>/cleanup-plan.json
python <skill>/scripts/closeout_artifacts.py --plan <experiment>/cleanup-plan.json --apply --journal <experiment>/cleanup.jsonl
```

执行器拒绝越界、盘根、目录候选、链接/junction/reparse路径，以及与系统规范路径不等的别名（含Windows短别名），不自动改写后放行；指纹变化、受保护项及删除集合中的保留者也拒绝。任一预检不安全时不删任何项。`temporary`允许的后缀仅为`.pyc/.pyo/.tmp/.part/.png/.jpg/.jpeg/.svg/.pdf`，还须有本轮所有权、真实生成来源且不属于保护集合；`.cache`、`.npy/.npz`等未知类型不自动开放，不要改名绕过。源码、数据、Notebook、模型等只能通过同字节副本规则清理。需要删除非重复旧模型时先完成领域留存判断，不能冒充temporary绕过执行器。

apply逐文件复核再unlink并落盘记录。运行中若文件被改动或删除失败，记partial和真实已删除项，非零退出；不承诺批量原子删除或恢复，不无限重试锁定文件。脚本不递归删除目录，也不改动保留文件。

## 磁盘和内存分开报告

- `planned_bytes`与`logical_bytes_removed`是文件逻辑大小，硬链接、压缩、回收站、云盘占位及并发写入会让物理空间变化不同；没有测量不能声称“已释放X GB”。仅移动到同盘归档不算释放。
- RAM由仍活着的进程占用决定。关闭本轮资源后可观察可用物理内存/commit，不把删除文件当成内存释放，也不把系统总体变化全归因于本任务。
- 最终一句话说清保留范围、实际删除项数/逻辑大小、未清理原因；清理记录放一份小清单，不加入用户要求仅两文件的提交ZIP。

## 依据与边界

- [DVC gc](https://doc.dvc.org/command-reference/gc)：先确定应保留的引用范围；共享缓存必须纳入其它项目，云端删除有不同风险。本流程只借鉴保留集合，不自动执行全局gc或清云端。
- [Snakemake protected/temp](https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#protected-and-temporary-files)：临时输出应在全部消费者结束后回收，昂贵输出需要保护；由此采用事先登记所有权和消费者，而非事后按名字猜。
- [MLflow gc](https://mlflow.org/docs/latest/api_reference/cli.html#mlflow-gc)：按生命周期删除不自动尊重UI置顶/模型标签。已归档、失败或置顶本身不能替代本项目的保留判断。
