# 后端契约与实施边界

当前为可运行的单机后端程序（0.3.0），同时分发skill。已实现：16份规则、Word/PDF逐页提取、真实DeepSeek多模态HTTP调用、SQLite任务与证据持久化、批量续跑、版本选择、教师逐项复核、本地正式成绩台账和CSV/JSON导出。没有前端、HTTP服务、教务系统对接或多人账号权限系统。原始报告只读。

Word输入优先采用[结构提取、分类与事实核对流程](word-first-workflow.md)，下文页面提取说明保留为PDF兼容及交叉核对层。新context增加evidence_plan及其指纹；binding原样增加evidence_plan_sha256。

## 数据流与职责

`原报告 → 版本/身份核对 → 文档渲染与证据提取 → 模型逐项判断 → 程序校验并汇总 → 教师复核 → 发布`

1. 入库层固定原文件哈希、实验编号、提交版本；同人不同文件不自动择新。文件名与封面比对，冲突/未知阻塞定分。仅遮盖文本层已知姓名和学号，图片内身份文字、班级、预填成绩不能保证去除，提示要求忽略；不宣称完成严格匿名化。实验15输出学号另由人工核对为true/false/unknown。
2. 提取层由Word只读导出PDF，核对页数后PDFium逐页渲染，保存正文及重叠图片裁片、页码、坐标和字节哈希。整页渲染覆盖浮动对象和截图；扫描图中文字清晰度仍需模型/人工判断。`extraction_complete`表示页面覆盖完整，不证明语义全部读对。`evidence/sources`仅为标准答案研究材料；学生证据独立保存在runtime。
3. 模型层看题目规则和报告证据，只判断档位，不决定权重、不做身份选择、不计算/发布总分。题目上下文可从对应规则和原题补入；不要把带答案图当成学生作答图。
4. 汇总层验证所有评分项恰好出现一次、证据存在、规则/报告/证据目录哈希一致；任何失败按任务异常处理，不回退为0分。
5. 人工复核层在原建议上增加有理由的改判事件，二次修改保留上次裁决，原模型判断另存。只有显式publish命令才会写入本地正式成绩台账；模拟成绩不能发布。没有向学校系统发送成绩的功能。

## 当前Python接口

`load_rubric('exp08')`读取规则；`fingerprint(obj)`对排序后的规范JSON计算SHA-256；`build_request(rubric, context, image_bytes, model=...)`返回Chat Completions请求体；`parse_response(response)`拒绝空内容、截断、错误和重复JSON键；`aggregate(rubric, judgments, context)`返回建议分与区间。

`context`由可信后端创建，**不能用模型返回值替换**：

| 字段 | 含义 |
|---|---|
| experiment_id | exp01—exp16，已核对的实验编号 |
| report_sha256 | 原提交文件字节SHA-256 |
| rubric_sha256 | fingerprint(完整规则对象) |
| evidence_sha256 | fingerprint(完整证据目录数组) |
| request_id | 单次请求唯一标识，补评另建关联请求，不复用旧响应 |
| model_requested | 本次请求模型名，默认deepseek-flash |
| extraction_complete | 是否已确认提取完整，严格布尔值 |
| identity_status | verified/conflict/unknown |
| blocking_flags | 后端检测的阻塞原因，如duplicate_submission_unselected |
| evidence | 证据数组，字段如下 |

每项证据含`id`、`kind`（text/code/image/terminal/identity）、`origin=student`、`locator`（页/段/图片位置）、`sha256`、`readable`。文本类含`text`且哈希必须与UTF-8文本匹配；图像哈希按发送的实际图片字节，若裁剪则另外保留原图哈希和裁剪位置于业务审计库。身份项含`match`。后端对身份检查结果负责，模型不得创建它。

模型输出仅含`binding`和`judgments`。binding原样回显以上6个绑定字段：experiment_id、report_sha256、rubric_sha256、evidence_sha256、request_id、model_requested。每条judgment必须含以下字段，不允许自带score/总分：

```json
{
  "criterion_id": "exp08.S01.C01",
  "verdict": "partial",
  "evidence_ids": ["p3-code1"],
  "observation": "代码对x=-5使用了错误的掩码，正数返回分支正确。",
  "reason": "只满足普通正数处理，未达到完整绝对值算法的满分条件。",
  "missing": false
}
```

缺答`missing=true`要求完整提取、全部材料可读，且引用已检索的全目录。无法确认是否缺答则unresolved，不强行zero。身份证据unknown时必须unresolved；实验15身份项不使用partial档。

汇总输出含`rows`逐项得分、`score_interval`、`suggested_score`、`blocking_flags`、`result_sha256`。`final_score=null`和`release_status=not_released`固定。证据存在校验**不能证明模型理解正确或截图一定真实**，语义判断仍需基准校准和教师复核。

## 业务接口建议（设计，尚未启动HTTP服务）

| 接口 | 责任 |
|---|---|
| POST /submissions | 上传只读原件，返回提交ID、哈希、候选身份及重复版本冲突 |
| POST /grading-jobs | 指定submission_id、实验、规则版本、模型配置快照；创建任务 |
| GET /grading-jobs/{id} | 返回提取状态、建议结果、逐项证据和待复核原因 |
| POST /grading-jobs/{id}/reviews | 教师逐项裁决，带reason与expected_revision，追加不可覆盖的审计事件 |
| POST /grading-jobs/{id}/publish | 要求已复核、无阻塞、提交/规则未变；原子发布所复核版本 |

建议实体：Submission（文件与版本）、Evidence（位置/哈希）、RubricVersion（不可变JSON）、GradingJob（配置与状态）、ModelAttempt（请求/响应摘要、实际model、usage、request_id）、CriterionDecision（档位与证据）、ReviewEvent、PublishedGrade。一个学生同一实验可有多份提交，但只能有一个显式选择的有效版本。不要用“同名文件最后出现者”替代版本选择。

任务状态为received → extracting → ready → judging → scored/needs_review → reviewed → published；解析/接口错误进入retryable_failed或manual_required，不走scored=0。请求重试使用相同业务幂等键与不同attempt ID，去重存档后再汇总。数据库发布与成绩版本记录在一个事务内；导出报告用outbox/状态回写，避免旧工具“数据库写成功、文件写失败”的分裂状态。与原工具相同的风险还包括实验切换后内部ID不更新，所以每个请求必须显式携带实验ID而非沿用UI/会话变量。

建议分、教师分和正式分分别存储。正式发布后改判需新事件和版本，不直接覆盖。保留申诉时能重放的输入、规则、模型配置、提取器版本及证据哈希；不要求保存模型隐藏推理。

以上HTTP接口仅为未来包装建议。当前实际入口为`Backend`和CLI：`import / select / prepare / run / batch / status / resolve / review / publish / export / recover / recheck`。实际状态为received、extracting、ready、judging、ready_for_teacher_review、needs_review、reviewed、published，以及extraction_failed、model_failed、retryable_failed。SQLite事务保护状态转换和发布；CLI逐个处理任务，单份失败不终止整批。网络超时可能已产生计费，不保证提供方恰好调用一次。

`recover`仅允许原本机工作进程已退出的任务恢复；仍存活的工作进程拒绝恢复。`recheck`只重新校验最后一次已保存的失败响应，不发送新请求、不挑最高分。程序对“missing=true但未检索完整目录”的零分改为unresolved，保存原判断及拦截原因；不补写证据、不直接给分。遗漏评分项、引用不存在的证据、绑定错误或JSON截断仍为任务失败。

本地结果以SQLite为准，文件为证据与导出快照。建议结果始终保留final_score=null；正式分在独立publications表和导出的published_score列。导出失败可重新导出到新目录，不影响已存数据库。当前无外部发布outbox，正式发布后的新改判应创建新任务并保留历史。

## 大报告与图像

底层构造器默认48张；后端配置默认160张、最多80页，单图8MiB、图像合计24MiB、请求体45MiB。这些是项目保守阈值，不是官方上限。超限明确失败，不丢图。按题拆分调度尚未实现，超限报告需人工处理或调整合理参数。

学生代码仅静态审阅；若以后要自动编译执行，应在隔离环境中另建验证服务，限制网络、文件访问及资源。本次不提供对本机直接执行报告代码的功能。

## 0.4.0与1.1.0-calibration扩展

允许minor，必须同时满足该冻结评分项minor_points非空及minor_credit具体条件。未设置minor的项和旧规则拒绝此档；执行项仍需实际图像/终端证据，题面示例不能给分，身份不设minor。其他full/partial/zero/unresolved契约保持；聚合器不接受总分，独立于同班其他成绩。

本机HTTP写操作带会话CSRF及当前修订号。教学报告revision与引擎job_revision分别检查。/tasks为持久化请求ID去重队列；/review重新运行确定性校验；/publish只接收当前review_id，不接受客户端总分。/export从数据库取模型建议、教师复核与正式发布三个值，不以网页草稿充当正式成绩。

文件优先导入、recommendation和review.accept_estimates扩展见[导入与重点复核](intake-and-priority-review.md)。严格result保持旧契约；接受推定仅在human_review和已验证的同绑定建议匹配时生效，逐项记录，身份不可推定。模型调用不能自行传入accepted_estimates放宽校验。
