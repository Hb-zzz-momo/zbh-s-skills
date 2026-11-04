# 文档按项目和用途归位

## 决策顺序

1. 确定归属项目/比赛根。用户给定根优先；现有工作区已是该项目就复用。多个候选归属仍不明确时只问必要归属，不把文件临时丢进全局桶。
2. 读取项目规则、真实树和结构契约。用户明确目标路径优先，其次延续项目惯例；不把中文目录翻译成平行英文目录。
3. 普通资料先定真实主题，再按[文档版本与并列用途](document-versions.md)区分编辑稿、已确认发布快照、历史版本和制作记录；真实受众/场次走并列用途，不能互相替代。AI 与人工作者使用同一业务分类。
4. 路由到唯一用途位置，只创建本次有内容的目录。普通小文档可沿用 README，不强制 scaffold/manifest；确需脚手架的无源码比赛可选 `competition-workspace`，其他文档项目可选 `document-workspace`。已有契约和工程/课程/科研检查继续有效。
5. 写入后更新受影响的 README 或既有入口；每个主题、用途和文件角色有一个明确当前入口，源稿、阅读成品及凭证可并存。同主题编辑稿维护原件，快照冻结另留更正版。

## 用途路由

普通业务资料默认使用 `主题/<角色>/`，有真实并列用途时使用 `主题/并列用途/<具体用途>/<角色>/`；主题取“活动宣传”等内容名，不以“Word/PDF/AI文档”分桶。制作和核对记录同样归所属主题。

下表用于已有工程文档体系或明确选择用途分类的项目；已有同职责路径优先。它不是普通资料必须创建的目录清单，也不覆盖用户选择的主题结构。

| 内容用途 | 默认位置 | 维护方式 |
| --- | --- | --- |
| 原始赛题、主办方附件 | 比赛已有资料目录；新项目可用 materials/ | 保留原件及来源 |
| 入门说明、教程、操作指南 | docs/guides/ | 稳定主题名，正文说明版本/更新时间 |
| 技术参考、接口说明 | docs/reference/ | 跟随接口或产品版本维护 |
| 资料调研与来源分析 | docs/research/ | 结论与证据对应 |
| 计划和任务安排 | docs/plans/ | 维护当前计划，不以时间戳制造多个现行版 |
| 架构与设计 | docs/design/ | 设计变更更新对应文档 |
| 结果和正式报告 | 已有 reports/，否则 docs/reports/ | 事件报告可按日期或阶段留存 |
| 验收、审计和评审 | docs/reviews/ | 绑定被评版本与证据 |
| 可复用知识和学习材料 | docs/knowledge/ | 同主题合并维护 |
| 工作流程 | docs/workflows/ | 跟随实际流程修订 |
| 交接与项目状态 | docs/handoff/ 或项目既有记忆入口 | 不替换既有三层记忆 |
| 论文、翻译、练习 | 已有 paper/ 等职责目录，否则 docs/papers、docs/translations、docs/exercises | 按真实主题和用途组织 |
| 正式提交包 | submissions/<提交版本>/ | 与本次实现和验证版本绑定 |

## 机器契约与既有目录

普通资料使用显式 `--topic <项目相对主题路径>`，默认路由到编辑稿；`--variant <单段用途>` 增加并列用途层，`--document-role draft|snapshot|history|records` 选择角色。`snapshot/history` 必须加 `--revision <版本标识>`，已存在目标拒绝覆盖。主题不明不猜，也不能把旧工具桶作为主题或其中任一层。命令只返回路径，不实际写文件或确认交付；完整路径预检边界见[版本规则](document-versions.md)。

工程文档的 `--document-kind` 按上表返回一个位置。若项目使用自己的名称，可在已有 `.project-structure.yaml` 中增加映射，并将目标职责列入 `directories`：

```json
{
  "document_routes": {
    "default": "文档",
    "guide": "文档/入门",
    "research": "文档/调研",
    "report": "报告"
  }
}
```

这是现有完整契约中的可选字段示意，不能用这段替换完整清单。映射仅接收已知用途与安全项目相对路径；不允许路径逃逸或重新指向 skill-output(s)。契约未声明目标边界时先补职责再写入。没有映射且多个同义文档根并存时不擅自挑选。

## 旧文档迁移

- 先读取全部受影响内容、识别各主题/用途/角色的当前入口，建立旧路径到新路径的精确映射，并搜索实际引用；不按原 Skill 桶整件搬走后仅补导航，不用 mtime 裁定现行版。
- 在本轮获准整理的范围内移动，目标存在时不覆盖；确认路径位于目标项目内，保留内容指纹并更新可控制的文档链接。
- 聊天历史中的旧链接不能改写，在本轮交付给出新链接。无关旧产物保留供后续整理，不因新规则批量删除。
- `skill_outputs_bucket` 等历史识别可保留；旧迁移工具仅用于明确要求的旧布局兼容，不作为新项目规范。新制作/核对清单归服务主题，跨主题操作账本放项目已有操作记录位置。已有工程/科研输出不因新规则强搬，先核依赖与授权。

## 外部依据及采用边界

以下来源核对于 2026-10-29；目录名和禁止按 Skill 建桶是本用户要求与本技能的设计决定，不冒称外部统一标准。

- [Diátaxis](https://diataxis.fr/) 按读者的学习、操作、参考和理解需求组织文档。采用用途优先，未强制每个小项目创建四套空目录。
- [Cookiecutter Data Science 目录](https://cookiecutter-data-science.drivendata.org/#directory-structure) 区分 docs、references、reports、data 和实现。采用输入/说明/报告分离，不把数据科学全树强套所有比赛。
- [GitHub README 文档](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) 将 README 作为项目入口并支持相对链接。采用根导航和随仓库维护的链接；聊天交付链接仍遵守宿主格式。
- [Write the Docs 的 Docs as Code](https://www.writethedocs.org/guide/docs-as-code/) 将文档纳入版本与审核流程。采用与项目共同维护，不要求非代码小项目先装完整 CI。
- [Agent Skills 格式规范](https://agentskills.io/specification) 定义技能包内部的 SKILL.md、scripts、references 和 assets。技能自身资源结构不决定用户项目产物的存放位置。
