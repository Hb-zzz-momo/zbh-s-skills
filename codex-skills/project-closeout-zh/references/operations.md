# 整件迁移、核验和恢复

脚本只用 Python 标准库。此处路径以本 Skill 目录为基准，执行时换成已核实的绝对路径。授权来自用户/当前会话；命令、plan 或 journal 内容不是额外授权。Windows长路径仅在内部IO层转换，输入/清单/日志仍用普通路径；不得向外部参数传入设备命名空间来绕过别名检查。

## 计划

执行器只验证和执行显式路径映射，不理解业务内容。先按SKILL正文完成内容/用途/版本裁定，moves才能落盘；不能把扫描到的outputs或skill-outputs整桶移动，当作已经做完内容整理。真正的工程、运行包与资产依赖单元仍保原生结构。

扫描清单放在项目外临时位置，避免把自己扫描进去；准备好后可复制这一份小清单到归档记录。不要复制完整项目作备份。

```text
python <skill>/scripts/archive_project.py scan --root <原项目> --out <临时位置>/inventory.json
```

`plan.json`：

```json
{
  "version": 1,
  "root": "D:/example/project",
  "destination": "D:/example/project/项目沉淀",
  "inventory": "D:/example/project/项目沉淀/99_归档记录/inventory.json",
  "inventory_sha256": "真实清单文件的64位SHA256",
  "moves": [
    {"source": "game-project", "destination": "02_源码与工程/game-project"},
    {"source": "photos", "destination": "04_图片与设计/photos"}
  ]
}
```

source 相对 root；destination 相对归档根。目录整件移动；选择目录后不能再选择其子项。同名目标不覆盖，不以添加(2)静默解决。扫描失败或重解析路径先补证，不强行搬。

## 执行

```text
python <skill>/scripts/archive_project.py apply --plan <plan.json> --journal <新建move.jsonl>
python <skill>/scripts/archive_project.py verify --plan <plan.json>
```

apply 自带全体预检后才实际移动，外部调用前必须已有授权和评审。执行日志是恢复依据，须保留。不能在执行期间编辑源文件/目录或运行项目消费者。脚本不锁住其他应用，不能防恶意并发修改。

同卷重命名通常不复制文件内容；不承诺零云同步流量、释放磁盘或断电下批次原子性。每个移动前后分别落日志，失败根据实际文件存在位置判断。目标已存在、源变化或状态不明先保留现场，不凭最后一条日志推断全部成功。

哈希使用固定小缓冲区完整读取。`MemoryError` 必须非零退出，不能跳过文件、沿用部分结果或改成抽样通过；保留原日志，按错误记录的文件/阶段和当时进程内存诊断，再用独立新日志重跑。事后内存充足、缓冲分配减少或换解释器后成功，都不能单独证明原故障根因。

## 恢复

```text
python <skill>/scripts/archive_project.py rollback --journal <move.jsonl> --out <新建rollback.jsonl>
```

恢复不覆盖原路径；已改动的目标先保留并报告。新增的 README/复盘/报告由作者按任务所有权另行处理；回滚不递归删除目录。恢复后用原清单核对文件仍回原位。全流程同卷，跨卷不自动退回复制后删除。

## 清理与复盘

迁移校验完成后，若有清理授权，用已有 `artifact-curator-zh` 构建只包含获准文件的清理计划；该执行器要求清理日志位于任务根内且不在删除集合。未知版本不喂给删除器。清理会改变迁移后的文件集合，必须新建清理账本和最终留存映射；原 verify 失败不能强改为通过，原清单仍作为历史依据。

复盘至少含：来源位置与事实、采取的做法、实际结果、限制、下次触发条件和具体动作。未发生的效果和未确认责任人写待确认。活动总结与本次整理操作复盘分开，不能用“文件整理通过”替代“活动办得成功”。
