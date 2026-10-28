# 文件位置路由规则

任何新文件先回答：责任是什么、谁拥有、是否共享、属于源码/配置/数据/输出/文档/测试中的哪一类、是否已有等价目录、依赖方向是什么。无法给出唯一目标时先返回 `CAUTION`，不要创建文件。

## 通用优先级

1. 用户明确路径。
2. 现有仓库中同类文件的稳定模式。
3. 适用 `AGENTS.md`、`PROJECT_STRUCTURE.md` 与 `.project-structure.yaml`。
4. 主蓝图的路由规则。
5. 框架惯例。

文档按[用途路由](document-routing.md)进入所属项目。AI作者或调用的Skill不是目录职责；不再新建 skill-output(s) 桶。代码技术栈未知时仍可先建立比赛/文档工作区。

## Web 与前端

| 责任 | 首选路径 | 约束 |
|---|---|---|
| 单一业务功能 | `src/features/<feature>/` 或 `frontend/src/features/<feature>/` | API、组件、hooks、routes、stores、types 可在功能内聚合 |
| 全局通用 UI | `src/components/ui/` | 不含业务专属状态和请求 |
| 跨功能组合组件 | `src/components/common/` | 必须有两个以上明确消费者；否则留在功能内 |
| 全局路由/Provider/布局 | `src/app/` | 只负责应用装配 |
| 功能私有 API | `src/features/<feature>/api/` | 仅该功能使用 |
| 共享 HTTP 客户端 | `src/services/` | 不包含具体页面逻辑 |
| 第三方库适配 | `src/lib/` | 隔离外部 API，不作为杂物箱 |
| 静态资源 | `src/assets/` 或 `public/` | 需构建处理的放前者，原样公开的放后者 |

## Python 后端

| 责任 | 首选路径 | 禁止混入 |
|---|---|---|
| HTTP 路由与依赖 | `app/api/routes/`、`app/api/dependencies/` | 核心业务算法、直接 SQL |
| 业务用例 | `app/services/` | Web 框架响应对象 |
| 数据访问 | `app/repositories/` | HTTP 解析和页面逻辑 |
| 持久化模型 | `app/models/` | API 序列化职责 |
| 输入输出模式 | `app/schemas/` | 数据库会话管理 |
| 数据库会话与迁移 | `app/db/` | 业务规则 |
| 横切配置/安全 | `app/core/` | 无作用域的工具函数 |

依赖方向应为 `api -> services -> repositories -> db/models`；schemas 可在 API 与服务边界使用。底层不得反向导入 HTTP 层。

## Monorepo 与微服务

- 可独立启动或部署的代码放 `apps/<app>/` 或 `services/<service>/`。
- Monorepo 有多个可选应用时必须明确指定 owner app；不得选中失败后回退到根 `src/`。
- 微服务内部代码放 `services/<service>/src/`，测试放同一服务的 `tests/`；先确认服务已存在，新服务先作为独立 `service` 边界创建并记录。
- 至少两个应用/服务消费的稳定代码放 `packages/<package>/`。
- 应用专属代码不得通过路径伪装进入 `packages/`。
- 服务间只通过明确 API、事件或 `contracts/` 交互；禁止跨服务导入内部源码。
- 基础设施文件进入 `infra/` 或仓库既有的 `infrastructure/`，不与应用源码混放。

## 科研、数据与机器学习

| 责任 | 首选路径 | 约束 |
|---|---|---|
| 工作流入口 | `steps/NN_<step>/run.py` | 只装配参数、输入输出并调用 `src/` |
| 步骤局部配置与说明 | `steps/NN_<step>/config.yaml`、`README.md` | README 写明输入、输出、依赖、运行命令 |
| 可复用算法 | `src/<package>/<domain>/` | 不放入 `steps/` 或 `notebooks/` |
| 实验配置和记录 | `experiments/<experiment>/` | 配置、说明、指标；大型制品外置 |
| 原始数据 | `data/raw/` | 只读，不覆盖、不放生成脚本 |
| 外部数据 | `data/external/` | 保留来源和许可 |
| 中间数据 | `data/interim/` | 可重新生成 |
| 建模输入 | `data/processed/` | 由受控流程生成 |
| 探索分析 | `notebooks/` | 验证后将可复用逻辑迁入 `src/` |
| 模型和图表等输出 | step 科研用 `outputs/`；数据科学用 `models/` 与 `reports/{figures,tables}/`；ML pipeline 用 `checkpoints/` 与 `outputs/{metrics,figures}/` | 以 manifest 已声明边界为准；不与源码混放 |

## Python 库

- 导入代码放 `src/<package>/`，测试放 `tests/`，使用文档放 `docs/`。
- 示例可放 `examples/`，但必须可运行且不得成为未测试的第二套实现。
- 构建、发布和测试配置保留在根级清单中；业务模块不得散落根目录。

## 目录创建门禁

创建前必须满足：没有等价职责目录；名称与层级一致；将容纳一类稳定文件；不是仅为一个临时文件；若改变蓝图已更新结构文档。禁止无作用域的 `misc/`、`temp/`、`others/`、`new/`、`backup/`、`common/`、`utils/`。

已有 `.project-structure.yaml` 时，候选主路径和伴随测试/文档必须都落在 manifest 声明的目录或其子孙中。条件目录尚未启用、manifest 损坏或多应用 owner 不明时均返回 `BLOCK`，先更新契约，不先写文件。

## 审计规则

- 根级出现应用源码：阻断并建议所属应用/包路径。
- `steps/` 中出现大段可复用逻辑：阻断并路由到 `src/`。
- 生成输出中出现源码、`data/raw/` 出现生成脚本：阻断。
- 共享包出现应用专属路径或命名：阻断。
- 只报告并建议最小迁移；除非用户明确授权，不自动移动现有文件。
