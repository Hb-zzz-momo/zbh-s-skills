# 命名规范

新项目采用本规范；现有项目若已有一致、清晰且无冲突的命名，则延续现有规范并在结构清单中记录差异。

## 通用目录

- 使用完整、可检索的职责名：优先 `frontend/`、`backend/`、`infrastructure/`，不要自行缩写为 `front/`、`back/`、`infra/`。若仓库已统一使用缩写则保留。
- 普通目录使用小写 `kebab-case` 或生态固定形式；同一层不得混用 `snake_case` 与 `kebab-case`。
- Python 包和模块使用 `snake_case`；包名必须是合法导入名。
- JavaScript/TypeScript 应用与包目录优先 `kebab-case`；React 组件文件遵循仓库既有的 `PascalCase.tsx` 或 `kebab-case.tsx`，不可混用。
- 目录名表达职责或领域，不表达时间状态。禁止 `new/`、`old/`、`temp/`、`backup/`、`final/`。
- 跨平台名称禁止 Windows 保留名、`< > : " | ? *`、控制字符、尾随空格/点及路径穿越；所有目标解析后必须仍位于项目根内。

## 研究和实验

- 有序步骤使用两位数字加职责：`01_data_acquisition/`、`02_data_cleaning/`。新增步骤取现有最大编号加一，不重编号历史步骤。
- 每个步骤入口固定为 `run.py`，局部参数为 `config.yaml`，契约说明为 `README.md`。
- 实验使用稳定 ID 与语义：`exp_001_baseline/`、`exp_002_ablation/`；不要只用日期或 `test1/`。
- Notebook 使用有序编号与目的，例如 `01_exploration/1.0-initial-data-exploration.ipynb`；可复用实现不得只存在 Notebook。
- 生成制品名称应包含实验/数据版本等可追踪信息，不用含糊的 `result-final-v2`。

## 应用、包、服务和功能

- 可部署单元使用角色名：`apps/web`、`apps/admin`、`services/api`、`services/worker`。
- 共享包按能力命名：`packages/ui`、`packages/types`、`packages/api-client`、`packages/config-eslint`。
- 功能目录用业务领域而非页面类型：`features/authentication`，不要创建 `features/forms` 作为跨业务杂物箱。
- API 路由、服务和仓储模块使用同一领域词汇，例如 `billing.py`，便于责任追踪。

## 模糊名称处理

只有在作用域清楚且目的写入局部规则时才允许 `common` 或 `utils`，例如 `src/features/search/utils/query-parser.ts`。根级或无所有者的 `common/`、`utils/`、`misc/`、`others/` 一律拒绝。

## 文件与配置

- 使用生态标准清单名，如 `package.json`、`pyproject.toml`、`compose.yaml`；不要创建同义副本。
- 本 Skill 的结构清单固定为 `.project-structure.yaml`，其内容为 JSON 兼容 YAML，便于零依赖解析。
- 项目职责文档固定为 `PROJECT_STRUCTURE.md`；作用域规则固定为 `AGENTS.md`。
- 忽略或生成目录名称遵循工具标准，如 `node_modules/`、`dist/`、`build/`、`.venv/`、`__pycache__/`，不为其创建职责条目。

## 改名门禁

改名属于迁移，不是普通结构修复。先列出引用、导入、构建脚本、部署配置、文档链接和历史制品影响；没有用户授权时仅提出建议，不执行批量改名。
