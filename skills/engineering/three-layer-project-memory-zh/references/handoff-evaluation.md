# 独立接班验收

由未获得预期答案的新 AI 或干净聊天只读项目入口和原件。真实请求：接手下一个实验，说明材料、当前规则、身份、有效成果、缺口与下一步。不提前提示缺陷或标准答案。

| category | 实际观察 |
|---|---|
| task | 找到材料与下一步，不把模板说成完成 |
| current-rule | 使用最新且范围适用规则，返回来源 |
| history | 排除被替代/失效事实，保留历史条件 |
| identity | 不串项目、学生、员工或机器 |
| unknown | 缺证据时明确未核验，不编造成绩 |
| sync | 隔离副本模拟缺失、变更或锁，应拒绝半同步 |

不改正式实验、不对外提交。破坏性案例仅在临时副本，清理前核对目标属于临时目录。

观察 JSON 必须有 snapshot_id、evaluator、method、cases；每个 case 包含 category、passed、observation（真实回答或工具证据）。六类全通过后 accept-handoff --input report.json。失败记录留 validation，修复后重测，不能自填 passed。

报告不参与同一 seal，避免循环；测试绑定 snapshot_id。程序只校验字段和绑定，不能证明语义正确。结构、内容、证据、快照、接班与实验验收分别报告。

回归运行 tests/test_memory.py；包括空模板、缺证据、更新、冲突、过期、范围隔离、预算、未知问题、半同步、CLAUDE 保留、拆分入口、旧 CLI 和真实项目使用。
