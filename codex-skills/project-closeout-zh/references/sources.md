# 来源与取舍

检索并打开原始来源：2026-10-27。范围为项目资料整理、个人数字保存、完整性清单与复盘方法，中文/英文检索并回原始提供者；这是定向网络调研，不代表穷尽全网，也未安装外部整理程序。

2026-10-28的v1.1修订由真实使用反馈触发：仅把生成器目录换位置仍找不到业务文件。落实为先读原件判用途/版本、日常入口按业务命名、生成记录分离、实际归位后由未读作者路线图者盲找。原v1.0的哈希/链接检查只证明安全完整，不作为此可用性要求的通过依据；本次没有为稳定本地材料重新宣称全网调研。

同日用户又指出“为什么多出来这么多文件夹”。因此增加目录数量复盘：区分业务目录、工程原生目录、技术记录，合并只重复文件名的单文件套层，不预建空模板；权限、历史版本隔离和工程依赖按真实用途保留。目录更少与容易找文件分别验收。维护证据见[内容与目录规则独立复核](content-routing-review.md)和[真实目录盲找及修订复验](findability-review.md)，其中保留首轮缺口，不能把找对文件冒充无需精简。

| 原始来源 | 采用到本技能 | 限制/未采用 |
|---|---|---|
| [Library of Congress：Taking Inventory](https://blogs.loc.gov/digitalpreservation/files/2016/05/pda_inventory.pdf) | 整理前先列内容、位置、格式、留存意愿和权限，保留以后回看的入口 | 不采集清单示例中的账号登录信息，不据此默认公开 |
| [Cambridge：Adding metadata](https://www.data.cam.ac.uk/organising-storing/metadata) | README 说明内容、时间、贡献/来源、打开方式和权利；资料需让接班者可理解 | 科研数据规范按项目需要裁剪，不要求活动产生 DOI 或完整科研档案 |
| [Tiago Forte：PARA 原文](https://fortelabs.com/blog/para/) | 已结束工作进入可检索的 Archives；活动内部按职责组织，避免仍活跃资料与历史混淆 | 不把所有电脑文件改成 PARA，也不把作者的效率主张当成本次实测收益 |
| [RFC 8493：BagIt](https://www.rfc-editor.org/rfc/rfc8493.html) | 借鉴“内容列全”和“逐项校验通过”分开；用清单与摘要证明迁移前后内容一致 | 当前目录不是 BagIt 包，未实现其 bagit.txt、data/、tag manifest 等约束，不能宣称符合 BagIt 标准 |
| [Atlassian：Retrospective](https://www.atlassian.com/team-playbook/plays/retrospective) | 复盘记录有效做法、问题和下次具体行动，负责人/期限只记录已确认值 | 不虚构会议、团队反馈、改善效果，不为文件整理强制开会 |

本地复用：`artifact-curator-zh` 已具备只读盘点、SHA256 与受限清理；`project-structure-architect` 控制目录职责；`three-layer-project-memory-zh` 恢复已有背景；`automation-error-learning-zh` 管来源和经验；`multi-agent-evaluation-zh` 分离作者与评审。本技能补项目结束后的分类、整件迁移、版本取舍、导航和可恢复验收，不替换这些能力。

不采用：只按扩展名分桶（会拆依赖）；只留所谓最新文件（证据不足）；全量再复制一份/反复ZIP（扩大占用）；给所有同字节文件创建硬链接（修改传播且云同步语义不同）；全局清缓存（超出项目）；按名称或年龄自动删除（无法证明无用）。
