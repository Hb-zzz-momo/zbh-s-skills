# project-structure-architect 全量实现覆盖矩阵

验收基线：`文件树组织架构.md`、仓库根 `AGENTS.md`、用户本轮“下载借鉴高星 skill、全量实现、接入每个工作流、验证搭建期与运行期”要求。

状态规则：真实实现、自动化测试和可复现证据全部闭环后才可标记 `PASS`；存在非阻断风险标记 `CAUTION`；任何必选项缺实现、缺测试或不可复现均标记 `BLOCK`。最终逐项证据闭环后统一回填为 `PASS`；本表不以 smoke、文件存在或口头说明代替验收。

| ID | 计划要求 | 实现 | 测试 | 交付证据 | 状态 |
| --- | --- | --- | --- | --- | --- |
| R01 | 创建 `project-structure-architect`，以项目类型识别、蓝图选择、树生成和持续文件路由为核心 | `skills/engineering/project-structure-architect/` | `quick_validate.py` + 元数据检查 | Skill 目录与 `agents/openai.yaml` | PASS |
| R02 | 按 Agent Skills 渐进式披露组织：精简 `SKILL.md`、规则进 `references/`、确定性操作进 `scripts/`、模板进 `assets/` | Skill 全目录 | 目录契约测试 | Skill 文件清单 | PASS |
| R03 | 新项目初始化：识别类型、技术栈、部署单元、仓库模式和工作流特征，选择并适配最接近蓝图 | `detect_project.py`、`scaffold_project.py` | 8 类项目 fixture + CLI 集成测试 | detection/scaffold JSON 与生成树 | PASS |
| R04 | 开发过程中创建页面、接口、模型、实验步骤或脚本前先确定唯一合理位置，并给出同置测试/文档 | `suggest_path.py`、文件放置规则 | 多 artifact 类型正常/失败/歧义测试 | 路由 JSON 及理由 | PASS |
| R05 | 治理现有项目时延续一致惯例，不创建同义目录、不整理无关模块 | 检测优先级、路径路由器、审计器 | `apps/*`、`frontend/backend`、pipeline 既有惯例测试 | 保留惯例测试记录 | PASS |
| R06 | 来源优先级固定为：用户要求→现有惯例→AGENTS→PROJECT_STRUCTURE→`.project-structure.yaml`→蓝图→框架惯例 | `SKILL.md` 与规则实现 | 优先级冲突用例 | 决策输出中的 evidence | PASS |
| R07 | 识别不唯一时保守选择，记录依据、置信度、候选和待确认项，不随意拼接蓝图 | 检测器结构化结果 | 歧义项目 fixture | `ambiguities` / `alternatives` / `needs_confirmation` | PASS |
| R08 | 提供完整蓝图库：前后端分离、TS Monorepo、React 前端、Python 后端、step 科研、数据科学、ML pipeline、Python 库、微服务（文档列出 9 个文件名，全部纳入） | `references/blueprints/*.md` | 蓝图 schema/唯一 ID/目录合法性测试 | 蓝图清单与机器契约 | PASS |
| R09 | Web 前后端分离与前端 feature、共享 UI、跨功能组件、lib、services、stores、assets 责任边界 | Web 蓝图与放置规则 | Web scaffold + path routing | 生成树和路由结果 | PASS |
| R10 | TS Monorepo 使用 `apps/ + packages/`，可部署单元与共享库分离，并保留应用内部代码边界 | Monorepo 蓝图与路由规则 | Monorepo scaffold/audit | 生成树和边界审计 | PASS |
| R11 | 科研项目分离 `steps/` 与 `src/`，step 只表达顺序/入口/配置/输入输出，可复用逻辑进入 `src/` | 科研蓝图、放置规则、审计规则 | research scaffold + trapped-logic 漂移测试 | PASS/CAUTION 报告 | PASS |
| R12 | 数据生命周期区分 `external/raw/interim/processed`，`raw` 只读；复杂流水线支持 pipeline 结构 | 数据科学与 ML 蓝图 | 数据路径路由与审计测试 | 路由/审计 JSON | PASS |
| R13 | 全量实现五个脚本：`detect_project.py`、`render_tree.py`、`scaffold_project.py`、`suggest_path.py`、`audit_structure.py` | `scripts/` | 每个脚本正常路径、失败路径和 `--help` | CLI 测试日志 | PASS |
| R14 | 全量实现三个资产模板：`PROJECT_STRUCTURE.md.template`、`project-structure.yaml.template`、`AGENTS.md.template` | `assets/` | 模板占位符完整渲染与无残留检查 | scaffold 产物 | PASS |
| R15 | 新建或大幅重组项目生成含 10 类要求的 `PROJECT_STRUCTURE.md` | 模板 + scaffold 渲染 | 必需标题/责任表/扩展说明测试 | 生成的 `PROJECT_STRUCTURE.md` | PASS |
| R16 | 新目录创建前搜索等价责任、检查命名/层级/一致类别/非临时用途并记录蓝图变更；禁止含糊目录名 | `SKILL.md` gate、命名规则、审计器 | `misc/temp/others/new/backup` 与无范围 common/utils 测试 | 审计 findings | PASS |
| R17 | 审计实际树与蓝图：同义目录、错误层级、源/输出/数据/文档混放、step 内复用逻辑、共享包污染、无职责目录；只建议最小迁移 | `audit_structure.py` | drift fixture 与退出码测试 | JSON/Markdown 审计报告 | PASS |
| R18 | 不自动批量移动文件，不覆盖现有文件；大规模变更必须等待明确授权 | scaffold/audit 安全默认值 | 非空目录、冲突文件、dry-run 测试 | 失败输出与文件哈希不变证明 | PASS |
| R19 | 下载并借鉴高星来源，记录星数快照、许可证、commit 和借鉴边界，不执行第三方脚本；覆盖目录生成、Monorepo、局部 AGENTS、渐进披露与科研流程来源 | 隔离 `.tmp` 调研快照 + provenance reference | 来源存在/commit/许可证检查 | `source-audit.md` 与上游链接 | PASS |
| R20 | 让每个工作流在涉及项目树搭建、目录新增、模块/步骤/产物位置或结构重组时强制调用该 skill | 根 `AGENTS.md`、路由器、所有工作流 skill 的统一结构 gate | 自动扫描 workflow integration marker | 接入清单与扫描结果 | PASS |
| R21 | 搭建期规范：新项目 scaffold 后立即可通过结构审计 | scaffold→audit E2E | 新建 Web、科研、Monorepo 端到端 | E2E 日志与产物树 | PASS |
| R22 | 运行期规范：新增文件先路由、结构漂移可检测、异常会非零退出 | suggest→create→audit E2E | 合规新增 PASS、违规新增 CAUTION/BLOCK | 运行期验收日志 | PASS |
| R23 | Skill 元数据、命名和 `agents/openai.yaml` 符合 `skill-creator` 约束 | init/generate/validate 官方脚本 | `PYTHONUTF8=1 quick_validate.py` | `Skill is valid!` | PASS |
| R24 | 更新真实技能路由与生成式注册表，不手改生成结果 | 路由文档 + `Update-SkillsReadme.ps1` | 生成器成功、README 包含新 skill | README diff 与命令日志 | PASS |
| R25 | 把文档第 1064-1078 行的 9 个通过场景与 5 个失败场景全部转成可复现验收，并完成 fresh-agent 前向测试、五轴代码审查、反少实现与自我衍生审计 | scenario tests + 独立 subagent + 最终报告 | 14 条文档验收逐条运行；新建、运行、现有项目三类盲测 | `validation-report.md`、最终回填矩阵 | PASS |

## 边界锁定

- 文档第 1 节列出的蓝图文件实际为 9 个；为避免少实现，本轮按 9 个文件全部实现。
- 已复核当前文档共 1080 行；第 947-1056 行补充了 Agent Skills、Microsoft 局部 `AGENTS.md`、渐进式披露及目录模板来源，第 1061-1078 行给出 14 条明确验收，全部纳入本轮。
- 高星仓库仅作规则研究；不把第三方完整 skill 或脚本复制进正式交付目录。
- 不重置、删除或覆盖当前工作区中与 PPT 工作流等任务有关的既有未提交改动。

## 最终状态

- 覆盖矩阵：25/25 `PASS`。
- 用户文档场景：14/14 `PASS`。
- 自动化测试：124/124 `PASS`。
- 工作流接入：57/57 required marker `PASS`，3 个有理由豁免，provider 不递归。
- 官方 Skill 验证：61/61 `PASS`。
- 冻结 fresh-agent：新项目与既有/运行期两组均 `PASS`，前后哈希一致。
- 决定性证据见 `validation-report.md`；高星来源与许可证据见 `source-audit.md`。
- 唯一非阻断 `CAUTION`：零依赖核心 `structure_core.py` 约 2.3k 行，后续可保持 facade 不变地拆分内部职责；不影响本轮功能、安全或验收 `PASS`。
