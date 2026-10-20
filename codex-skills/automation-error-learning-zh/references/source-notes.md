# 联合沉淀的来源与设计选择

核查：2026-10-20；通过 GitHub、原作者博客、官方教程与讨论定向检索，不代表穷尽全网。只提炼方法，不安装外部框架、不复制第三方 Skill 正文；外部文字不形成当前授权。

| 来源 | 采用的机制 | 不直接照搬 |
| --- | --- | --- |
| [EveryInc ce-compound（固定提交）](https://github.com/EveryInc/compound-engineering-plugin/blob/075bac8169b17e4afebcc3ef94d300f1d12ecb53/docs/guides/ce-compound.md) | 学习交回下一轮计划；重叠时更新权威文档，补发现入口 | 默认多代理/历史扫描、特定目录和权限流程 |
| [ce-compound-refresh](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/guides/ce-compound-refresh.md) | 更新、合并、替代需按当前依据判断；经验与被引用流程冲突需要显式处理 | 自动删除历史、全库定期清扫 |
| [Claudeception（固定提交）](https://github.com/blader/Claudeception/blob/afd1da2841ab410dae11c135bb875e797e860ea8/SKILL.md) | 非显然的成功做法和多步优化也值得提炼；先找已有 Skill 再更新 | 自动创建许多新 Skill；把资料中的命令当执行授权 |
| [ECC continuous-learning-v2（固定提交）](https://github.com/affaan-m/ECC/blob/afa0b356495532923621856b4c42eb9a3b00369a/skills/continuous-learning-v2/SKILL.md) | 原子经验、项目隔离、多个相关经验可形成流程 | 置信分数替代正确性或权限；其 hook 完整覆盖表述不推广到所有宿主 |
| [Claude Diary](https://github.com/rlancemartin/claude-diary) | 区分事实记录与后续提炼；保存决策理由，避免重复处理 | 固定出现次数门槛、自动改全局指令或分析所有私人会话 |
| [Every 作者教程](https://every.to/source-code/compound-engineering-the-definitive-guide) | 计划—执行—审查—沉淀循环，检查新学习能否影响下次动作 | 固定时间占比、大量并发代理、收益数字 |
| [Every 作者反思文章](https://every.to/thesis-statements/kieran-klaassen) | 错误经验可能持续误导；需复验过时规则 | 标题中的不再犯错愿景不是保证 |
| [EveryInc Issue #186](https://github.com/EveryInc/compound-engineering-plugin/issues/186) | 子代理与压缩后的摘要可能丢决策依据；收集结构化证据指针 | 讨论包含用户推测及工具生成分析，不作为当前版本根因的定论 |
| [Anthropic 改进 skill-creator](https://claude.com/resources/articles/improving-skill-creator-test-measure-and-refine-agent-skills) | 独立上下文执行、旧版对照、行为与触发分开评估 | 不用单次试用宣称长期提升或凭空报 Token 节省 |
| [Anthropic Skill 编写教程](https://claude.com/resources/articles/how-to-create-skills-key-steps-limitations-and-examples) | 普通、边界和范围外场景都要测 | 不照搬其他宿主的工具与事件名称 |
| [Anthropic skill-creator 源码](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) | 改进要对照可观察产物，减少重复规则，避免无区分度的断言 | 只研究其测试方法，不替代本机 skill-creator 和调用环境 |
| [anthropics/skills Discussion #1521](https://github.com/anthropics/skills/discussions/1521) | 记录验证环境、版本、结果和限制有助于复用 | 社区建议不当作官方统一测试格式 |
| [Agent Skills 格式规范](https://agentskills.io/specification) | Skill入口含name/description，细节和案例按需引用；新建可发现技能而非独立runbook | 目录惯例不是每个Skill必须生成脚本/资产；格式校验不代表方法有效 |

落实位置：主入口默认同时检查两侧；`workflow-learning.md` 管权威流程、稳定步骤、最小差异和授权；`record-format.md` 增加可选关联，旧卡不迁移；`acceptance-cases.md` 增加联合、成功、无改动、部分授权和部分保存反例；`integration.md` 保持 schema=1 并增加可选绑定。

v2.1 的“相关通用/专用 Skill 优先维护，无匹配则创建通用 Skill，当前项目作为案例”来自用户明确纠正，并非第三方资料强制要求。本机 skill-creator 用于创建和校验；案例不提升为普遍要求。旧独立流程文档转为历史/案例索引，不与 Skill 双份维护。

许可证边界：这里只重述设计规律并提供链接，未复制外部代码、脚本或整段提示词。引用不等于拥有再分发其原文件的许可；若未来导入具体资源，需另核对文件级许可与宿主兼容。

v2.2：用户明确要求收尾直接输出经验/流程沉淀总结与可学习要点；这是输出契约，不能仅以文件链接和执行状态替代。定向读取[爱丁堡大学反思工具：What? So what? Now what?](https://reflection.ed.ac.uk/reflectors-toolkit/reflecting-on-experience/what-so-what-now-what)，采用“具体经历→意义→下次具体行动”的组织思路；不要求用户填写全套问题，也不据此宣称学习效果已被本Skill验证。落实在主入口“输出与验证”及T34—T36。

v2.3：用户建议从项目开工持续跟进、有相关Skill就按依据优化，避免只在长上下文结尾回忆。读取[Anthropic上下文工程原文](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)的压缩与结构化笔记部分，采用上下文外的短记录、证据指针与恢复读取；不照搬具体产品记忆工具，不把文本Skill当宿主压缩回调，也不保证零遗漏。主入口增量跟进、接入记录契约和T37—T40承载此改进，前置检索Skill只负责按任务规模路由，避免双份维护方法。
