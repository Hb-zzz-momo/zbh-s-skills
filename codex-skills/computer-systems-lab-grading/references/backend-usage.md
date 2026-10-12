# 单机后端运行指南

这是可运行程序，skill封装的是同一套程序和16份评分标准。输入Word/PDF，输出逐项证据、建议分或待复核区间；教师复核分和本地正式分分别记录。无需前端。

Word默认使用[结构优先流程](word-first-workflow.md)，通常先核对事实、再评分，两次模型调用。新流程结果见runtime/structured-pilot；本文末尾97.5及75—100属于旧页面流程历史值。

## 环境与入口

Python 3.10以上，安装本项目：`python -m pip install .`；需要PDFium和Pillow。旧doc和docx转换还需要Windows安装Microsoft Word。PDF可跨平台。开发验证另外运行`python -m pip install ".[test]"`。

项目入口为`python scripts/run_backend.py`，默认数据存入项目runtime。独立skill入口为`python scripts/run.py --data-root <独立数据目录>`，需同样安装pypdfium2和Pillow；不要把学生数据存进skill分发目录。以下示例在grading-backend目录运行，SUBMISSION_ID、JOB_ID、REVISION等均替换为上一步输出值。

```powershell
python scripts/run_backend.py doctor --credentials "C:\Users\zbh\OneDrive\Desktop\deepseek.txt"
python scripts/run_backend.py validate
python scripts/run_backend.py import "..\实验报告\实验2" --experiment exp02
python scripts/run_backend.py status --submissions
```

doctor只检查依赖/密钥是否配置，不发送报告、不回显密钥，也不证明接口在线或Word转换成功。密钥优先取DEEPSEEK_API_KEY，否则从指定文件读取。配置也可放JSON后通过--config指定，字段见deepseek.md。现有任务始终用创建时配置，修改配置后应prepare新任务。

## 单份试批与批量

```powershell
python scripts/run_backend.py prepare SUBMISSION_ID --credentials "C:\Users\zbh\OneDrive\Desktop\deepseek.txt"
python scripts/run_backend.py run JOB_ID
python scripts/run_backend.py status JOB_ID
```

prepare保留原件副本，生成PDF、逐页图片、重叠裁片和证据目录。run才调用DeepSeek。文件名和封面不一致、读图困难或缺答依据不足会阻塞确定评分。姓名和学号只做有限文本层遮盖；图片内部身份文字未保证全部去除。

同人同实验发现不同版本时，不按文件顺序覆盖，先指定有效版本：

```powershell
python scripts/run_backend.py select SUBMISSION_ID --actor "教师姓名" --reason "采用截止时间前确认的版本"
python scripts/run_backend.py batch --experiment exp02 --limit 5 --credentials "C:\Users\zbh\OneDrive\Desktop\deepseek.txt"
python scripts/run_backend.py batch --experiment exp02 --limit 5 --send --credentials "C:\Users\zbh\OneDrive\Desktop\deepseek.txt"
```

不加--send只准备证据；加--send才发送。每次最多处理limit个可处理任务；已完成/待教师复核的任务不重复评分，单份错误记下后继续。存在未选版本的提交不处理，通过status --submissions查看。不要为求高分不断重试；修复原因后再恢复处理。

## 复核、发布与导出

人工先查看runtime中对应任务的PDF/图片和suggestion.json。`review`需要操作人、原因以及当前revision，防止旧页面或旧脚本覆盖新裁决。无--decisions表示逐项确认当前结果；有未解决项或身份冲突时会拒绝确认。

```powershell
python scripts/run_backend.py review JOB_ID --reviewer "教师姓名" --reason "已逐项核对原图" --revision REVISION
python scripts/run_backend.py export "runtime\exports\第一次试批"
```

需要改判时把更改项写入JSON数组，用`--decisions changes.json`。每项包含criterion_id、verdict、evidence_ids、observation、reason、missing，格式见backend-contract.md；只列实际修改的项。程序按固定满分/部分分档重新计算，不接受自由总分。二次复核继承上一次裁决，原模型结果保留。

只有教师明确决定发布时才执行：

```powershell
python scripts/run_backend.py publish JOB_ID --review-id REVIEW_ID --revision REVIEW_REVISION
```

publish只写本机正式成绩台账，不对接教务。要求当前选定版本、最新复核、无未解决项且非模拟结果；不直接修改原报告。建议对象里的final_score始终为空，正式分看publications或导出的published_score，不能把suggested_score当正式成绩。

导出目录必须不存在。scores.csv区分建议分、区间、教师分、正式分、状态和版本是否选中；criteria.csv是**模型建议及程序拦截后的逐项结果**，人工最终裁决见对应*-reviewed.json。失败记录的分数为空，绝不填0。原始响应、尝试次数和审计事件在SQLite，导出供查看而非替代数据库。

## 异常处理

| 状态/问题 | 处理 |
|---|---|
| extraction_failed | 检查Word/文件损坏后执行retry-extraction JOB_ID；改变报告应重新import |
| retryable_failed | 修复网络后run；超时可能已经计费，记录每次尝试 |
| model_failed | 查看错误；无效JSON或漏项保持失败，不能强行给分；提示/规则改变需新prepare |
| needs_review | 查看未解决项并人工裁决，不以区间下限作为成绩 |
| identity/title阻塞 | 人工核对后resolve JOB_ID --reviewer ... --reason ... --verify-identity或--clear-flag FLAG |
| 实验15输出身份 | resolve ... --output-id-match true/false，证据绑定改变后必须重新run |
| 进程退出但状态仍extracting/judging | recover JOB_ID --reviewer ... --reason ...，只恢复已退出的本机工作进程 |
| 已存模型响应需新校验逻辑 | recheck JOB_ID，不重新调用模型，仅处理最后一次失败响应 |

文件上限64MiB、80页、默认160张裁片；超限明确报错，不截掉后面内容。后台不执行学生代码，不根据文风或相似度自动认定作弊。已有班级名单与文件优先自动归属导入；严格图片匿名化、多人权限和分布式队列尚未实现。本版适用于教师本机操作；具体建议分和重点复核见[导入与重点复核](intake-and-priority-review.md)。

## 本次验证范围

实验2/3各一份已实际发送给用户指定DeepSeek接口。实验2得到97.5建议分；实验3部分缺答缺乏完整检索依据，保留75—100待复核区间，未确定总分。未发布任何真实学生成绩。16份规则均有结构/分值验证，但仅两份真实试批，尚未完成教师标注校准，不能据此声称已证明公平。
