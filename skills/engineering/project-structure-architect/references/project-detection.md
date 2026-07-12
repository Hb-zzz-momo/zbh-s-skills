# 项目识别规则

在选蓝图或创建目录前完成识别。不要只按编程语言分类，也不要把单个依赖视为确定结论。

## 识别维度

| 维度 | 候选值 | 需要回答的问题 |
|---|---|---|
| 用途 | Web、前端、API、科研、数据科学、机器学习、库、CLI | 仓库最终交付什么？ |
| 技术栈 | React、Vue、Next.js、Node.js、FastAPI、Django、Spring、Python | 哪些框架决定目录边界？ |
| 部署 | 单体、前后端独立、多应用、多服务 | 哪些单元能独立构建、测试、部署？ |
| 仓库 | 单项目、语言 Monorepo、多语言 Monorepo | 是否共享版本、工具链和包？ |
| 工作流 | 请求响应、定时任务、数据流水线、有序研究步骤、实验 | 是否存在输入输出明确的连续阶段？ |
| 既有规范 | `frontend`、`backend`、`apps`、`packages`、`src`、`steps` 等 | 仓库已经稳定使用什么？ |

## 证据强度

按“结构证据 > 构建清单 > 依赖文本 > 文件名猜测”排序。至少记录命中的路径和推断，不只输出类型名。

| 证据 | 候选蓝图 | 强度与说明 |
|---|---|---|
| `frontend/` 与 `backend/` | `web-fullstack-separated` | 强；两个明确边界 |
| `package.json`、`turbo.json`、`apps/`、`packages/` | `web-typescript-monorepo` | 强；工作区与多应用共同出现 |
| React 依赖及 Vite/Next 配置 | `react-frontend` | 中；若同时存在后端证据则需消歧 |
| Vue/Svelte 依赖 | `react-frontend` 的最近前端蓝图 | 中；必须标记真实技术栈并返回 `CAUTION`，确认 adaptation 后才搭建 |
| `pyproject.toml` 中含 FastAPI/Django | `python-backend` | 中；还要排除库和研究仓库 |
| `data/`、`steps/`、`src/`、`experiments/`、`outputs/`、`paper/` | `research-step-based` | 强；有序科研交付链 |
| `data/raw`、`data/interim`、`data/processed`、`notebooks/`、`models/`、`reports/` | `data-science` | 强；数据生命周期明确 |
| `src/*/pipelines/`、`experiments/`、`checkpoints/` | `machine-learning-pipeline` | 强；模块化训练流水线 |
| `pyproject.toml`、`src/<package>/`、`tests/` | `python-library` | 强；src-layout 库 |
| 多个 `services/*/Dockerfile` 与 `infra/` | `microservices` | 强；多个独立部署单元 |
| `Snakefile` | 科研或 ML 流水线候选 | 中；结合数据、实验和论文目录判断 |

## 决策过程

1. 读取用户要求、根级及适用的嵌套 `AGENTS.md`。
2. 枚举根目录、两层内关键目录和构建清单；忽略生成目录、依赖缓存和大文件内容。
3. 记录六个维度的证据，不对空目录编造用途。
4. 对每个蓝图累计支持证据和冲突证据。
5. 只有一个明显领先候选时选定；证据并列、冲突或为空时返回 `CAUTION` 并要求确认。
6. 现有项目中，稳定重复的结构优先于理想化蓝图。选定蓝图只用于审计和增量扩展，不授权迁移。

## 保守原则

- 空目录不得自动选蓝图。
- 仅有 `package.json` 且同时出现 React 与后端依赖时，不得假定是前后端分离还是单体。
- 已有 `apps/web`、`apps/api`、`packages/*` 时，不因用户新增一个页面就创建 `frontend/`。
- 已使用 Kedro、Snakemake 等 Pipeline 框架时，不额外引入编号 `steps/`。
- 多种蓝图确需组合时，在 `PROJECT_STRUCTURE.md` 的“决策与例外”中记录主蓝图、借用部分和原因。

## 识别结果契约

识别结果至少包含：`status`、`classification`、`selected_blueprint`、`evidence`、`ambiguities`、`alternatives`、`needs_confirmation`。状态含义：唯一且证据充分为 `PASS`；可继续但需确认或存在非阻断冲突为 `CAUTION`；此阶段不应因“不够理想”自动返回 `BLOCK`。
