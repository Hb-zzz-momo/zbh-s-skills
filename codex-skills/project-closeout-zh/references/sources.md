# 来源与取舍

检索并打开原始来源：2026-10-27。范围为项目资料整理、个人数字保存、完整性清单与复盘方法，中文/英文检索并回原始提供者；这是定向网络调研，不代表穷尽全网，也未安装外部整理程序。

| 原始来源 | 采用到本技能 | 限制/未采用 |
|---|---|---|
| [Library of Congress：Taking Inventory](https://blogs.loc.gov/digitalpreservation/files/2016/05/pda_inventory.pdf) | 整理前先列内容、位置、格式、留存意愿和权限，保留以后回看的入口 | 不采集清单示例中的账号登录信息，不据此默认公开 |
| [Cambridge：Adding metadata](https://www.data.cam.ac.uk/organising-storing/metadata) | README 说明内容、时间、贡献/来源、打开方式和权利；资料需让接班者可理解 | 科研数据规范按项目需要裁剪，不要求活动产生 DOI 或完整科研档案 |
| [Tiago Forte：PARA 原文](https://fortelabs.com/blog/para/) | 已结束工作进入可检索的 Archives；活动内部按职责组织，避免仍活跃资料与历史混淆 | 不把所有电脑文件改成 PARA，也不把作者的效率主张当成本次实测收益 |
| [RFC 8493：BagIt](https://www.rfc-editor.org/rfc/rfc8493.html) | 借鉴“内容列全”和“逐项校验通过”分开；用清单与摘要证明迁移前后内容一致 | 当前目录不是 BagIt 包，未实现其 bagit.txt、data/、tag manifest 等约束，不能宣称符合 BagIt 标准 |
| [Atlassian：Retrospective](https://www.atlassian.com/team-playbook/plays/retrospective) | 复盘记录有效做法、问题和下次具体行动，负责人/期限只记录已确认值 | 不虚构会议、团队反馈、改善效果，不为文件整理强制开会 |

本地复用：`artifact-curator-zh` 已具备只读盘点、SHA256 与受限清理；`project-structure-architect` 控制目录职责；`three-layer-project-memory-zh` 恢复已有背景；`automation-error-learning-zh` 管来源和经验；`multi-agent-evaluation-zh` 分离作者与评审。本技能补项目结束后的分类、整件迁移、版本取舍、导航和可恢复验收，不替换这些能力。

不采用：只按扩展名分桶（会拆依赖）；只留所谓最新文件（证据不足）；全量再复制一份/反复ZIP（扩大占用）；给所有同字节文件创建硬链接（修改传播且云同步语义不同）；全局清缓存（超出项目）；按名称或年龄自动删除（无法证明无用）。
