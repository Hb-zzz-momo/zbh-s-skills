# Delegation Runbook

## 总原则

父代理是主执行者和验收者。子代理是并行探索、独立实现或只读审计线程。

不要因为任务复杂就自动开子代理。只有用户明确授权 subagent、`/sub`、并行代理、委派或 worker/explorer 时，才进入真实调度。

## 父代理职责

- 解释用户真实目标和边界。
- 选择本地主 skill。
- 判断是否需要 `plan-faithful-execution-zh` 锁边界。
- 决定哪些任务留在关键路径本地执行。
- 分配子代理角色、写范围、等待点和验收标准。
- 集成 worker 结果。
- 运行本地验证和审计。
- 决定最终结论、论文 claim、发布判断和交付状态。

## 子代理职责

每个子代理只拥有一个 bounded job：

- 一个具体问题。
- 一个输入上下文包。
- 一个输出契约。
- 一个停止条件。
- worker 额外要求一个互斥写范围。

子代理不得扩展任务范围、修改未授权文件、替代本地审计、直接宣布最终验收。

## 默认流程

### Step 1: 授权检查

| 用户表达 | 行为 |
|---|---|
| 明确说 `/sub`、subagent、子代理、并行代理、委派 | 可进入真实调度 |
| 只说全面、深入、仔细、全量分析 | 不真实调度，除非用户追加授权 |
| 要求“用多个代理帮我” | 可进入真实调度 |
| 要求“不要开子代理” | 必须父代理本地执行 |

### Step 2: 本地主流程

先确定本地主 skill：

| 场景 | 主流程 |
|---|---|
| 工程实现 | `skill-router-zh` + `agent-skills-ao` 生命周期 |
| 中文项目开发 | `project-dev-zh` |
| 科研多候选 | `research-skill-flow-zh` |
| 科研实验执行 | `research-experiment-ops-zh` |
| 结果或论文 claim | `decisive-result-audit-zh` / `paper-writing-zh` |
| 长任务运行 | `agent-wait-monitor-zh` |

### Step 3: 关键路径拆分

把任务拆成：

- **父代理立即做**：下一步必须依赖的 blocker、集成判断、写范围裁决。
- **子代理并行做**：读审、检索、独立文件范围实现、独立测试、最终 review。
- **禁止委派**：最终论文 claim、formal 结论、发布验收、用户边界裁决。

### Step 4: 角色选择

| 类型 | 工具角色 | 权限 | 用途 |
|---|---|---|---|
| explorer | `explorer` | read-only | 代码地图、文献证据、日志审计、未知点调查 |
| worker | `worker` | write | 独立实现、测试补充、互斥文件范围 |
| reviewer | `explorer` 或 read-only worker | read-only | 最终审查、风险扫描、claim 边界 |

默认优先 explorer。worker 只在并行收益大于集成成本时使用。

### Step 5: 等待策略

- 不要把立即 blocker 交给子代理后空等。
- 子代理运行时，父代理做不重叠的本地工作。
- 只有下一步必须用到子代理结果时才 `wait_agent`。
- 若子代理部分失败，父代理根据已有信息继续或降级，不要重复开同类代理。

### Step 6: 集成验收

worker 返回后：

1. 父代理检查改动路径是否在授权范围内。
2. 检查是否回滚或覆盖他人改动。
3. 运行相关验证。
4. 必要时调用本地 review/audit skill。
5. 决定接收、修正、重跑、退回或放弃。

## 工程运行模式

### 单 explorer

适合：

- 不确定代码入口。
- 需要先理解调用链。
- 需要独立 review 一个风险面。

父代理继续本地读关键文件，不等待 explorer 时不要重复做同一问题。

### worker + reviewer

适合：

- worker 修改独立文件范围。
- reviewer 最后只读审查。
- 父代理有明确验证命令。

不要让 reviewer 在每个小改动后都运行。默认放在最后。

### 两个 worker + reviewer

适合：

- 两个 worker 写范围完全不重叠。
- 接口 contract 已确定。
- 父代理能清晰描述合并顺序。

如果 shared schema、配置或公共函数会被两边改动，退化为串行。

## 科研运行模式

### 文献 / 历史记录并行 intake

父代理：

- 用 `research-skill-flow-zh` 建候选池。

子代理：

- explorer A：读文献和证据。
- explorer B：读历史实验、raw、summary、失败路线。

回收：

- 候选结论进入 Gap Gate。
- 不直接生成 paper claim。

### 候选创新点并行 smoke 设计

允许多个 explorer 分别审查候选，但每个候选必须保留：

- 痛点。
- 假设。
- 创新点。
- 证据。
- smoke 验证方式。
- 失败条件。

进入 dev/formal 前仍必须收敛到一个主候选或明确组合候选。

### formal / claim 审计

不能交给普通子代理直接裁决。必须回到：

- `decisive-result-audit-zh`
- `research-iteration-audit-zh`
- `paper-writing-zh`

## 证据目录

substantial 子代理运行推荐记录：

```text
subagent-runs/<run-id>/
  orchestration-plan.md
  status.md
  worker-briefs/
  results/
  review-verdict.md
  acceptance.md
```

若任务属于 skill 输出，也可放入：

```text
skill-outputs/subagent-orchestration-zh/<中文主题_YYYYMMDD_HHMMSS>/
```

## 退化策略

| 情况 | 处理 |
|---|---|
| 当前运行时没有 subagent 工具 | 明说不可真实调度，父代理本地执行 |
| 用户未授权真实 subagent | 只给本地方案，不 spawn |
| 写范围冲突 | 串行或单 worker |
| 子代理结果不完整 | 父代理补最小缺口或重新规划 |
| 子代理结论影响论文/发布 | 触发本地审计 skill |
