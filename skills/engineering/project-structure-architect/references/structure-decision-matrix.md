# 结构决策矩阵

先确定部署边界，再确定目录蓝图。目录不是按语言数量决定，而是按所有权、构建和部署边界决定。

## 蓝图选择

| 场景 | 主蓝图 | 根级骨架 | 选择条件 |
|---|---|---|---|
| 前后端独立构建或不同技术栈 | `web-fullstack-separated` | `frontend/ + backend/` | 两个部署单元；可选 `contracts/` |
| TypeScript 多应用或共享包 | `web-typescript-monorepo` | `apps/ + packages/` | 至少两个应用，或一个应用与明确共享包 |
| 单一 React 前端 | `react-frontend` | `src/app + src/features + src/components` | 一个前端部署单元，无独立后端 |
| Python 单体 API/后端 | `python-backend` | `app/api + app/services + app/repositories` | 一个后端部署单元 |
| 有序科研过程 | `research-step-based` | `data + steps + src + experiments + outputs + paper` | 步骤顺序本身需要被表达 |
| 通用探索和分析 | `data-science` | `data/raw/interim/processed + notebooks + src + models + reports` | 数据生命周期重于部署 |
| 模块化训练/数据 Pipeline | `machine-learning-pipeline` | `src/<package>/pipelines + experiments + checkpoints` | 节点依赖与可复用流水线是核心 |
| 可发布 Python 包 | `python-library` | `src/<package> + tests + docs` | 导入包和发布边界清晰 |
| 多个独立服务 | `microservices` | `services + packages + infra` | 每个服务独立构建、测试、部署 |

## 容易混淆的边界

| 候选 | 选择前者 | 选择后者 |
|---|---|---|
| 前后端分离 / TS Monorepo | 多语言或前后端工具链独立 | 应用和共享包由统一 JS/TS 工作区管理 |
| 科研步骤 / 数据科学 | 需要显式执行顺序、论文和实验记录 | 以探索、数据加工和报告为主 |
| 科研步骤 / ML Pipeline | 人可读的阶段顺序是核心 | 可组合节点、训练管线和模型制品是核心 |
| Python 后端 / Python 库 | 运行服务、API 和数据库访问 | 发布/复用导入包，无应用层 |
| Monorepo / 微服务 | 共享工具链与包是主要边界 | 服务独立部署且基础设施契约重要 |

## 条件目录

条件目录只有条件成立才生成：

- `contracts/`：前后端或服务间存在共享 API、事件或数据契约。
- `infrastructure/` / `infra/`：确有容器、网关、部署或 IaC 文件。
- `packages/`：存在明确消费者或架构边界；不得为未来猜测创建空包。
- `paper/`：交付包含论文、补充材料或投稿包。
- `checkpoints/`：训练确实产生本地模型检查点，并应进入忽略规则或制品存储。
- `notebooks/`：用于探索；生产实现仍应进入 `src/`。

## 组合规则

1. 选择一个主蓝图，主蓝图决定根级目录和依赖方向。
2. 只借用另一个蓝图中与明确需求对应的子树，不拼接整棵树。
3. 写明借用目录的所有者、依赖方向、生成条件和退出条件。
4. 不创建同义目录，例如同时存在 `infra/` 与 `infrastructure/`、`app/` 与 `apps/`、`utils/` 与 `common/`。
5. 现有仓库若已采用一个清晰等价名称，继续使用它，并在清单中记录别名。

## 新建与治理

- 新项目：可按蓝图创建必选目录；条件目录由用户需求或显式开关决定。
- 现有项目：默认只审计和给出新文件路径；不得自动移动、删除或改名。
- 大规模调整：先生成迁移映射、影响面与回滚方案，并获得用户授权。
- 完成标准：每个创建的目录都有用途，文件路由能给出唯一首选路径，运行后审计仍不产生结构漂移。
