# 整个项目的历史覆盖

项目记忆包含全部已做工作。当前状态是历史的最新切面；接班需要知道过去为什么这样做，哪些方案失败、哪些结果可复用。保存可追溯历史，启动时按任务加载，不把全部聊天塞进上下文。

先从用户的项目范围、目录、报告、日志、修订记录和必要的相关聊天建立工作清单。文件缺失不等于工作没做过；用户确认做过而执行证据未找到时，保留确认的出处，将过程和结果记为缺口，不能编造，也不能用其他同学材料补齐。只保存与项目决策或复现有关的过程，不抄无关闲聊。

每个工作项至少定位八项：

| facet | 内容 |
|---|---|
| requirements | 当时的任务、题目与适用授权 |
| inputs | 原讲义、数据、环境与身份来源 |
| process | 真实操作顺序、实现路径、关键尝试 |
| outputs | 结果、产物位置与验收范围 |
| revisions | 版本顺序、替代关系、为何重做；无修订须有依据 |
| issues | 错误、失败、未解决问题与限制 |
| lessons | 由过程得出的经验、适用条件、不可推广之处 |
| evidence | 原件、日志、Notebook、截图、核验记录及哈希 |

manifest 示例：
```json
{"history_units":["work-1"],"history_catalog":"docs/project-entry/结果/历史覆盖.json"}
```
catalog 示例（实际项目必须替换来源记录）：
```json
{"project_id":"demo","units":[{"id":"work-1","evidence_status":"documented","facets":{"requirements":["work-1-input"],"inputs":["work-1-input"],"process":["work-1-process"],"outputs":["work-1-output"],"revisions":["work-1-process"],"issues":["work-1-process"],"lessons":["work-1-lesson"],"evidence":["work-1-output"]}}]}
```

facets 关联当前可信、同项目的 records；process 至少关联 episode，lessons 至少关联 procedure。可让同一记录承担有实际内容的多个栏目，不能只写“已有资料”假装全覆盖。大量原过程留第三层或原 evidence，record 摘要带关键词、别名、来源定位和 related_ids。

若证据不齐，evidence_status=evidence_gap 并给非空 gaps 列表。八项仍须有记录指明已知内容或未知原因。程序只检查目录与引用；独立接班测试检查语义覆盖，尤其不能把“待补过程”误认为真实过程。输出 history_coverage.evidence_gaps 必须保留在交付说明。

历史事件发生于过去，但“那次发生了什么”的记录仍可 confirmed 且默认检索。失效的是旧规则或被替代的当前状态，不是历史本身。保留旧事件、失败原因和修订链；新规则不会抹去旧批次。经验至少包含触发条件、处理、验证与推广边界，不将某次最小修复授权或特定模型参数推广到后续实验。

验收先查工作清单是否覆盖用户声明的全部已做范围，再问新 AI：过去各项做了什么？版本为何改变？常见失败如何解决？哪里仍缺证据？仅能回答下一步计划不合格。
