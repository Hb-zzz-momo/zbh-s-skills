# 本地交付验证

日期：2026-10-19。结论：PASS，限本机 Windows 的静态任务范围；不承诺所有项目的性能无损或固定 token 节省比例。

执行者 `/root`；独立脚本评审 `/root/snapshot_review`；独立前向场景评审 `/root/workflow_review`。两个评审初评使用独立上下文，未互看结论。七项运行资源冻结版本为 r2，摘要见 [输入哈希](tests/frozen-r2-hashes.json)；原始意见、修订及复验分别见 [评审 B](tests/review-B.md) 与 [评审 C](tests/review-C.md)。保留 r1 的真实 BLOCK，未用作者自评覆盖。

| 用户方案 | 实际交付与核验 |
| --- | --- |
| 代码地图、证据地图 | assets/maps.md 含指定字段、原路径/身份/版本及来源定位；按已有项目索引补字段，非自动全库解析器；C 样例核验 |
| 状态哈希、只读变化范围 | 标准库 CLI check/record、完整 SHA256、范围绑定、失效与异常降级；真实 CLI 和16项测试 |
| 每任务按需记忆与收尾整理 | SKILL.md 规定3–8条软目标、原话/归纳/来源区分、长期候选类别；只在原任务收尾写候选，不自动改全局记忆或启动后台服务；C 场景核验 |
| 低风险压缩与保护块 | 默认抽取式摘要/导航，保护数字、代码命令、引用来源、模板验收、身份路径；C 三份材料包保持保护块同一 SHA256；不安装压缩模型 |
| 独立评审精简包 | 保留完整目标/验收、冻结版本、原证据和按需追加读取；不削弱既有代理人数要求；真实三评审长期收益未测 |
| 保守性能与执行边界 | 小任务旁路、64文件/8MiB每件/32MiB合计、2秒协作式预算；无常驻/网络/模型/新依赖/全局钩子，超限回到原流程 |

验证命令（Python 需本机可用，不为本技能安装运行时）：

```powershell
python -X utf8 -B -m unittest discover -s 'C:\Users\zbh\.codex\skills\context-budget-guard-zh\tests' -v
python -X utf8 'C:\Users\zbh\.codex\skills\.system\skill-creator\scripts\quick_validate.py' 'C:\Users\zbh\.codex\skills\context-budget-guard-zh'
```

结果：16/16测试通过，无跳过；技能校验通过。额外真实 CLI 观察覆盖已有嵌套缓存目录、首次观察、只读无变化、变化归属、新增清单、64文件/32MiB合法边界及总量超限。最终本机样例（含启动）小清单约179–207ms，32MiB检查约451ms；不代表通用性能基准或节省比例。完整本轮工作记录位于任务工作区 `skill-validation/context-budget-guard-zh/`。

r1发现与r2修订：Windows创建时间不能识别读后写入再还原mtime，现改用真实ChangeTime复查；缓存目录校验后被替换可能向范围外创建锁，现record在首次写锁前固定目录与祖先句柄。新增三项回归均通过。输入未加拒写锁；目录内正常写入、原子保存及子进程写入由独立评审实测可用。record期间缓存/祖先目录改名暂时被拒绝，正在重组目录时应跳过record；异常后句柄释放已验证。

结构审计：使用既有技能包惯例 SKILL.md/agents/assets/references/scripts/tests；源码、资源、测试与原始评审分开；无同义目录、嵌套仓库、生成缓存或二进制。通用项目蓝图检测不识别技能集合，其CAUTION不冒称自动PASS；按用户明确创建本机技能及skill-creator规范完成针对性结构核验。没有修改其他技能或全局入口。

未验证：真实大项目长期节省率、Word/PDF渲染或课程实验正确性、平台/云同步状态、压缩模型与长期记忆平台。本技能不提供这些领域结论，不以本验证代替它们。
