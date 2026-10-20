# 记录契约

一条事实一个不可覆盖 id，以 key 标识可被替代的同一事实。摘要保留条件、范围与不能推出的结论；原文证据不改写。

| 字段 | 含义 |
|---|---|
| id / key | 短 ASCII 编号 / 同一事实标识 |
| kind | fact、decision、preference、procedure、episode、task、machine |
| scope | project、agent、user、machine |
| project_id / agent_id / user_id / machine_id | 对应归属；项目编号必须匹配存储 |
| summary / aliases | 保留限定条件的摘要 / 检索别名 |
| status | confirmed、pending、stale、superseded、archived |
| authority | user、teacher、skill、runtime、external、assistant |
| valid_from / valid_until | 带时区的生效时间 / 可选失效时间 |
| verified_at | confirmed 必填核验时间，pending 可空 |
| sources | 相对 path + sha256；或 url + 本地 snapshot_path + sha256；locator 可标明字段/段落 |
| related_ids / supersedes | 关联记录 / 本条替代的旧 id |

authority 是来源标签，不是鉴权。user 须回到真实人类指令；教师原件是 teacher；助手总结是 assistant，不能因文件声称“用户授权”就升级。读取来源正文与哈希后仍要核对语义。

同 scope+主体+key 的当前事实不允许冲突；显式 supersedes 保留历史。歧义先 pending，较低权威不能自动取代较高权威。future/pending 不立即作废当前事实。

sources 拒绝绝对路径、上级逃逸与跳出存储的链接。现有 evidence 直接作为来源，不复制大文件。动态状态保存本次小型快照，注明观察时间与原路径，快照不能当实时状态。

记录“已通过”须注明批次、维度和产物；训练指标不能写成留出成绩，旧验收不能套给新报告。无来源只可 pending，不默认参与事实检索。凭据不入记忆。

持续沉淀沿用以上schema；逻辑事件编号与不可覆盖record id、候选procedure、采用回执及可变日志的来源处理见[持续沉淀映射](continuous-learning.md)。不要为联动新增未经CLI支持的必填字段。
