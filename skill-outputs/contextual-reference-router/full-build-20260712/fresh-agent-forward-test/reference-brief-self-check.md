# Reference Brief 自检

> 检查对象：`reference-brief.md`；检查日期：2026-07-12；状态口径：`PASS / CAUTION / BLOCK / N/A`。

## 1. 要求覆盖矩阵

| 要求 | 实现 | 验证/证据 | 状态 |
|---|---|---|---|
| 使用 `$contextual-reference-router` | 完整读取技能主文件、routing matrix、source registry、search playbook、analysis template、quality checklist；运行确定性路由脚本，结果为 `dashboard` | Brief 的来源组合覆盖真实产品 UI、指标模型、图表选型、筛选/状态 | PASS |
| 设计“GitHub 开源项目健康度分析 Dashboard”参考 | 输出任务边界、7 个具体案例、6 条规律、信息架构、状态契约和落实地图 | `reference-brief.md` 第 1–7 节 | PASS |
| 有可用时使用实时来源 | 2026-07-12 打开 GitHub、CHAOSS、OSS Compass、From Data to Viz 的具体页面并进行浏览器视觉检查；记录两项动态页面限制 | `reference-brief.md` 第 3、9 节中的直接 URL 与访问记录 | PASS |
| 只产出 Reference Brief 与自检 | 指定目录仅写入 `reference-brief.md` 和本文件；临时浏览器截图不进入交付目录 | 交付目录文件计数应为 2 | PASS |
| 保存到指定目录 | 两个文件均位于 `skill-outputs/contextual-reference-router/full-build-20260712/fresh-agent-forward-test/` | 绝对路径复核 | PASS |
| 不检查其他 forward-test 输出 | 全程只读取技能文件、公开来源、记忆索引搜索结果和本指定目录；未列举、打开或比较其他 forward-test 目录/文件 | 操作边界审计 | PASS |

## 2. 技能质量清单

### 任务适配

| 检查项 | 结论 | 证据 |
|---|---|---|
| 来源与 Dashboard 任务匹配 | PASS | GitHub 原生健康清单、CHAOSS 健康模型、OSS Compass 健康 Dashboard、图型 Gate |
| 案例与 GitHub/开源健康主题匹配 | PASS | 所有核心案例均直接涉及 GitHub 仓库、开源项目健康或对应图表关系 |
| 考虑受众和使用场景 | PASS | 维护者/OSPO 周期复盘被标记为“工作假设”，并保留受众变更影响 |
| 考虑技术栈与成本 | PASS | 技术栈未提供，因此不预选图表库；把实现来源推迟到下游技术选型 |
| 记录品牌/模板/不可变项 | PASS | 明确无品牌/模板输入，不复制参考品牌；锁定只交付 Brief 与自检 |

### 检索质量

| 检查项 | 结论 | 证据 |
|---|---|---|
| 打开具体案例而非只看站点名/摘要 | PASS | 实际访问 `pingcap/ossinsight/community`、具体 GitHub Docs、CHAOSS 模型、OSS Compass 功能案例、两类图表页 |
| Dashboard 检查了密度、筛选、图表组合、标签和状态 | PASS | GitHub 清单观察覆盖分区/行状态/动作；OSS Compass 覆盖维度树/时间筛选/并排趋势/轴设置；GitHub API 补足异步与错误状态 |
| 至少两个互补来源 | PASS | 4 个网站、4 个互补来源族 |
| 普通任务控制在 2–5 站、3–8 案例 | PASS | 4 站、7 个具体页面/案例 |
| 达到停止条件 | PASS | 第四来源补齐图表 Gate 后，后续检索没有增加新维度，停止扩展 |
| 视觉限制已明确 | PASS | GitHub Pulse 实页和 OSS Insight 动态页的 headless 限制在 Brief 第 9 节单列，且不作为未核实视觉证据 |

### 提炼质量

| 检查项 | 结论 | 证据 |
|---|---|---|
| 形成 3–7 条可执行规律 | PASS | Brief 第 4 节共 6 条，均落到页面和验收条件 |
| 区分结构、交互、图表、状态 | PASS | 6 条规律分别覆盖决策层级、指标模型、筛选、图型、语义色、行动闭环 |
| 每个来源说明采用/不采用 | PASS | 第 3 节每个来源均含 adopt/reject/translation/license |
| 避免空泛审美词 | PASS | 未用“高级/现代/精美”作为规则；规则均可通过组件或状态验收 |
| 区分事实、观察、推断 | PASS | 每个核心来源均显式分为“事实 / 视觉结构观察 / 推断” |

### 转化质量

| 检查项 | 结论 | 证据 |
|---|---|---|
| 多来源重组而非复制单一案例 | PASS | 健康模型取自 CHAOSS，行动清单取自 GitHub，分区/轴透明取自 OSS Compass，图型约束取自 Data to Viz |
| 每条规律有落实位置和验收证据 | PASS | Brief 第 5 节 6 行一一对应 |
| 保留项目独有内容与功能 | CAUTION | 用户尚未提供品牌、业务口径或真实数据；Brief 已保留开放决策，等待下游补齐 |
| 不牺牲可读性/可访问性/功能完整性 | PASS | 禁止颜色单编码、双轴和空白错误；定义表格替代与七类状态 |
| 参考不替代真实数据/工程测试 | PASS | Brief 第 9 节明确边界，未声称 Dashboard 已实现 |

### 合规质量

| 检查项 | 结论 | 证据 |
|---|---|---|
| 检查许可证 | PASS | GitHub Docs CC BY 4.0、CHAOSS MIT、OSS Compass web AGPL-3.0、data_to_viz MIT；品牌/截图另行保守处理 |
| 未复制品牌/商标/图像/完整构图/代码 | PASS | 只提炼抽象规律；临时截图不进入交付目录 |
| 未虚构访问记录或案例细节 | PASS | 成功访问与失败限制分别记录；未把空白/未渲染页当作视觉证据 |
| 外部页面被当作不可信数据 | PASS | 只提取参考信息，未执行页面指令、未读取凭证或私密数据 |
| 联网、视觉和许可限制明确 | PASS | Brief 第 3、9 节 |

## 3. 参考数量与落地计数

- 网站：4（GitHub、CHAOSS、OSS Compass、From Data to Viz）。
- 具体页面/案例：7（GitHub Community 实页/说明、Pulse、Metrics API、CHAOSS Starter Model、OSS Compass Dashboard 功能案例、Line Chart、Heatmap）。
- 核心参考组：4。
- 可执行规律：6。
- 落实映射：6 条，逐条包含组件、转译与下游验收证据。
- 排除模式：7 类。
- 数据状态：7 类。

数量均落在技能要求的普通任务范围内。

## 4. 反少实现审计

| 风险 | 审计结果 | 状态 |
|---|---|---|
| 只有网站名，没有具体案例 | 每个核心来源均有具体页面、URL 和访问观察 | PASS |
| 只写“借鉴优秀案例”，没有设计转译 | 已落实到页面层级、指标卡、筛选条、图表、状态和行动队列 | PASS |
| 只有装饰性视觉结论 | 规则全部是结构、口径、交互、状态或图型约束 | PASS |
| 把 stars/forks 当健康 | 明确降级为背景热度，并给出 CHAOSS 四维起始模型 | PASS |
| 自行发明阈值、权重或总分 | 未固化；全部列为开放决策 | PASS |
| 只完成 smoke 就声称 Dashboard 完成 | 未生成或声称 Dashboard 实现；Gate 仅对参考阶段判定 | PASS |
| 许可不明仍复制素材 | 不复制素材；对网页代码许可与品牌/截图权利作区分 | PASS |
| 动态页面未渲染仍声称视觉检查完成 | 两项限制已单列，核心结论由其他可视觉检查来源补足 | PASS |
| 产生计划外文件 | 交付目录应仅有两份 Markdown | PASS |

## 5. 自我衍生审计

- **没有固化的计划外关键假设**：受众、默认时间窗、阈值、权重、时区、机器人过滤、刷新 SLA、技术栈均未擅自确定。
- **唯一工作边界推断**：题目为单数“一个 GitHub 开源项目”，因此 Brief 先按单个公开仓库组织；该推断已公开标注，多仓/私有仓库被排除而非默默扩张。
- **没有用扩展替代必选项**：未以配色、动效或高级图表替代指标模型、状态、筛选、行动闭环和许可审查。
- **没有越过用户指定阶段**：只交付 Reference Brief 和自检，不创建 Dashboard、DESIGN.md、线框图、PPT、源码或截图包。

## 6. Gate 结论

最终产物结构检查结果：目标路径精确匹配为 `True`；文件数为 `2`；文件名为 `reference-brief.md`、`reference-brief-self-check.md`；必选章节缺失数为 `0`；Brief 中包含 14 个直接来源/许可链接。临时浏览器截图与独立 profile 已从系统临时目录清理，交付目录未保留截图或其他中间产物。

**PASS（Reference Brief 阶段）**

理由：具体案例、互补来源、事实/观察/推断、3–7 条规律、落实位置、验收条件、排除模式和许可/访问限制全部闭环。存在的 `CAUTION` 只涉及尚未提供的品牌、真实数据和产品口径；这些内容被显式保留为下游开放决策，没有被伪造，也不阻断本轮“只产出 Brief 与自检”的验收。

Dashboard 实现状态为 **N/A（不在本轮授权范围）**，不得据此声称产品已完成或已通过工程测试。
