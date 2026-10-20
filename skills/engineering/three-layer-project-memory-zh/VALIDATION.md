# v2 验收覆盖

| 要求 | 实现 | 验证 |
|---|---|---|
| 三层保守初始化与拆分 | initialize / manifest.overviews | 空模板、split、CLAUDE |
| 来源、时间、状态、替代 | validate_record / put_record / set_status | 证据、过期、冲突、权威 |
| 项目/员工/用户/机器隔离 | namespace / retrieve | 四种主体与外部 store |
| 别名、排序、预算、拒答 | tokens / retrieve | alias、budget、unknown |
| 原子写入与锁 | atomic_text / writer_lock | 并发、id 不可覆盖 |
| 索引、关联与维护 | changed / rebuild_index / audit | 索引、缺失关联 |
| 来源变化、批次完整性 | seal / verify_snapshot | 证据变化、半同步、旧测试失效 |
| 接班与实验分开验收 | audit / accept_handoff | 绑定测试及独立观察 |
| 全项目历史覆盖 | history_coverage / manifest.history_units | 漏工作/漏栏目/失效引用阻断，证据缺口显式保留，历史事件默认检索，历史接班案例必需 |
| 真实 CLI 与旧参数顺序 | main | 单测与实际项目 |

运行：`py -3 -m unittest discover -s skills/engineering/three-layer-project-memory-zh/tests -v`。
最终结果保存 tests/results/validation.json。项目应用与身份资料只存项目内，不上传公开技能仓库。

## v2.1持续沉淀联动

本批不改脚本或schema；检验入口去重、事件→既有records映射、pending边界、稳定来源及阶段封存，方法见[持续沉淀映射](references/continuous-learning.md)和[联动接班场景](references/handoff-evaluation.md)。保留原单测及CLI门禁，不用文档联动替代真实接班测试。运行结果、真实独立评审和未验证项记录在当前任务的私有交付记录，不将个人材料放入公开Skill。
