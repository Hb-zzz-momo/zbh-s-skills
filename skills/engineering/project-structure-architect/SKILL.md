---
name: project-structure-architect
description: "项目与比赛目录规划和持续治理：在启动及新增文件前确定项目归属、目录职责和唯一存放路径，支持文档先行、比赛准备和各类工程蓝图。文档按业务用途归位，保留既有目录并审计结构漂移。用于新建项目、项目初始化、比赛文件夹、AI文档存放、文件路由和结构整理；不因生成文档就强制创建代码工程。"
---

# Project Structure Architect

把项目需求转换为可维护的目录蓝图，并在后续开发中持续回答“这个文件为什么应当放在这里”。核心闭环是：检测、选蓝图、脚手架、文件路由、结构审计；Git 提交检查只属于外围验证。

## 不可跳过的结构门禁

在新建或移动应用、服务、包、模块、页面、API、研究步骤、实验、流水线、测试、文档或多文件产物树前，执行以下门禁：

1. **触发门槛**：本轮是否会初始化目录、创建新的职责类别、改变部署边界或重组现有结构。
2. **前置证据**：读取当前及父级 `AGENTS.md`、现有树、`PROJECT_STRUCTURE.md`、`.project-structure.yaml`、构建 manifest 和用户要求。
3. **禁止越界**：不得静默套统一模板、创建同义目录、覆盖现有文件、移动无关模块、把源码与数据/输出混放，或为了偏好蓝图大规模改造清晰的现有结构。
4. **判定结果**：使用 `PASS / CAUTION / BLOCK`。只有依据唯一、目标路径明确并可验证时才是 `PASS`。
5. **下一步动作**：`PASS` 才进行结构写入；`CAUTION` 只做 dry-run、报告或补证据；`BLOCK` 停止结构写入并修正或询问用户。

纯内容编辑且路径已被用户或现有规范唯一确定时，不重复设计蓝图；仍须遵守最近作用域的结构规则。

## 来源优先级

按以下顺序裁决，不得为了更喜欢某个蓝图而颠倒：

1. 用户当前明确要求。
2. 一致的现有仓库惯例。
3. 当前路径适用的 `AGENTS.md`。
4. `PROJECT_STRUCTURE.md`。
5. `.project-structure.yaml`。
6. 最接近的本 Skill 蓝图。
7. 框架惯例。

若高优先级来源互相冲突，列出具体冲突并停在 `BLOCK`；不得自行选一个。若检测不唯一但来源不冲突，给出保守推荐、候选、证据与 `CAUTION`，待确认后再 scaffold。

## 核心工作流

### 0. 先确定项目归属与文档用途

- 当前工作区已经是一个项目或比赛根时直接复用；处于多个项目的共同父目录时，先定位真实目标，不能另建同名套娃目录或全局输出桶。
- **所有新文档都按项目及用途存放**，包括 AI 生成的指南、调研、计划、设计、报告、审计和学习笔记；禁止默认使用 `skill-output/`、`skill-outputs/<skill-name>/`、`AI文档/`。调用了哪个 Skill 不决定文档归属。
- 用户明确指定路径或文档目标时优先遵从；已有 `文档/`、`reports/`、`paper/` 等约定时沿用，必要时记录 `document_routes`，不机械新建同义 `docs/`。
- 技术栈尚未确定的比赛选择 `competition-workspace`，其他文档先行项目选择 `document-workspace`；建立根阅读入口和最小文档边界后即可写资料，不必先有源码。
- 原始赛题、附件与生成说明分开；机器日志/缓存仍按运行职责管理。持续维护的文档使用稳定主题名并更新原件，仅事件记录或提交快照带日期。目录按本轮实际用途创建。

生成文档或修复旧默认路径前，读取[文档用途路由与迁移](references/document-routing.md)。

### 1. 检测项目

先运行：

```powershell
python scripts/detect_project.py <project-root>
```

检查结构化输出中的：

- `classification`：用途、部署、工作流和仓库模式。
- `technology_stack` 与 `existing_conventions`。
- `selected_blueprint`、`alternatives`、`ambiguities` 和 `evidence`。
- `needs_confirmation` 与状态。

检测空的新目录只能得到 `CAUTION`；此时依据用户需求从[结构决策矩阵](references/structure-decision-matrix.md)选择蓝图，不得伪称自动识别成功。需要了解完整标志、得分和歧义规则时读取[项目检测规则](references/project-detection.md)。

### 2. 选择并读取一个主蓝图

按检测结果直接读取对应蓝图：

- 前后端独立部署：[web-fullstack-separated](references/blueprints/web-fullstack-separated.md)
- TypeScript 多应用：[web-typescript-monorepo](references/blueprints/web-typescript-monorepo.md)
- React 单前端：[react-frontend](references/blueprints/react-frontend.md)
- Python API/后端：[python-backend](references/blueprints/python-backend.md)
- 有序科研步骤：[research-step-based](references/blueprints/research-step-based.md)
- 通用数据分析：[data-science](references/blueprints/data-science.md)
- 模块化 ML/数据流水线：[machine-learning-pipeline](references/blueprints/machine-learning-pipeline.md)
- Python 库或 Python CLI：[python-library](references/blueprints/python-library.md)
- 多独立服务：[microservices](references/blueprints/microservices.md)
- 比赛启动与资料工作区：[competition-workspace](references/blueprints/competition-workspace.md)
- 文档先行项目：[document-workspace](references/blueprints/document-workspace.md)

默认只使用一个主蓝图。技术栈适配只能调整该蓝图内的条件目录、包名和局部文件；若必须组合多个蓝图，先在 manifest 的 `adaptations` / `exceptions` 中写明原因和边界。

### 3. 搭建新项目

先 dry-run，再正式创建：

```powershell
python scripts/scaffold_project.py <target> --blueprint <id> --project-name <name> --dry-run
python scripts/scaffold_project.py <target> --blueprint <id> --project-name <name>
python scripts/audit_structure.py <target>
```

用户已明确技术栈时用可重复的 `--technology` 精确写入分类，例如
`--technology React --technology FastAPI`。蓝图条件目录只能通过显式
`--enable-option <name>` 启用；先从所选蓝图读取支持的 condition 名称，未知选项必须失败。

脚手架必须生成或渲染：

- 选中蓝图的目录树。
- `.project-structure.yaml` 机器契约。
- 含分类、树、职责、放置、命名、依赖、新增方法、生成/忽略目录、决策与例外的 `PROJECT_STRUCTURE.md`。
- 根级及适用的局部 `AGENTS.md`；已有同名文件一律保留。

目标非空时默认拒绝。只有用户明确要求在现有目录补齐缺项时才使用 `--allow-existing`；该模式仍不得覆盖文件，结果最高为 `CAUTION`。

### 4. 运行期路由文件

在目的地不明显或将引入新职责类别时运行：

```powershell
python scripts/suggest_path.py <project-root> --artifact <type> --name <file> --owner <scope-owner>
```

文档可使用 `--artifact documentation --document-kind guide --name 赛题入门指南.md`，返回用途路径而不写文件。支持 guide、reference、research、plan、design、report、review、knowledge、workflow、handoff；未指定用途保留一般文档路由。新文件写入后更新真实阅读入口，不能只生成目录树却让用户找不到正文。

Monorepo 有多个可选应用时还必须传 `--application <apps 下的应用名>`；未指定时返回
`BLOCK` 和候选应用，不得回退到根 `src/`。

每次决策至少回答：职责、所有者、复用范围、文件类别、既有等价目录、输入/输出，以及同置测试或文档。只接受一个 `path`；返回 `alternatives` 或 `needs_confirmation` 时不得创建文件。

前端 API 的确定性分流是：单一 feature 私有调用放 `features/<feature>/api/`；跨 feature 的共享客户端放 `services/`。`common` / `utils` 仅在父级已经给出清晰 owner 时允许，例如 `components/common` 或 `src/<package>/utils`；根级无范围目录为 `BLOCK`。完整规则见[文件放置规则](references/file-placement-rules.md)和[命名规范](references/naming-conventions.md)。

新增科研步骤时使用脚手架的 step 模式；自动取现有最大编号加一，不重编号旧步骤，并创建入口、局部配置和输入/输出 README。`steps/` 只负责编排，可复用算法进入 `src/`。

### 5. 治理现有项目

先只读渲染和审计：

```powershell
python scripts/render_tree.py <project-root> --max-depth 4
python scripts/audit_structure.py <project-root>
```

审计必须覆盖：蓝图缺项、同义/含糊目录、根级源码、源码与生成输出混放、`steps/` 内的大型复用逻辑、共享包中的应用私有代码、raw 数据污染、无职责顶层目录和文档/manifest 漂移。审计器只报告最小迁移建议，绝不自动移动文件。

已有 `apps/ + packages/`、pipeline 框架、`front/` 等一致惯例时延续它们；结构问题与用户本轮功能改动分开报告。

## 确定性脚本

| 脚本 | 用途 | 写入行为 |
| --- | --- | --- |
| `scripts/detect_project.py` | 识别分类、技术栈、惯例、候选蓝图和歧义 | 只读 |
| `scripts/render_tree.py` | 生成稳定排序的目录树，默认排除生成目录 | 只读 |
| `scripts/scaffold_project.py` | 新项目脚手架或新增编号科研 step | 默认 dry-run 可预览；正式模式只新增、不覆盖 |
| `scripts/suggest_path.py` | 给出唯一文件路径、理由和伴随文件 | 只读 |
| `scripts/audit_structure.py` | 检测结构漂移并给出规则 ID | 只读 |

所有 CLI 必须支持 `--help`，以 UTF-8 向 stdout 输出 JSON（树文本位于 `render_tree.py` 的 `tree` 字段），并使用统一退出码：`PASS=0`、`CAUTION=1`、`BLOCK=2`、`ERROR=3`。已有 `.project-structure.yaml` 一旦损坏或不符合 schema，路由和结构写入必须先 `BLOCK`。

## 渐进加载索引

- 需要识别信号、得分或保守选择规则时，读取[项目检测规则](references/project-detection.md)。
- 需要判定蓝图、adaptation 与 combination 边界时，读取[结构决策矩阵](references/structure-decision-matrix.md)。
- 需要新增具体文件、目录或伴随测试时，读取[文件放置规则](references/file-placement-rules.md)。
- 需要目录/文件/step/experiment/notebook 命名时，读取[命名规范](references/naming-conventions.md)。
- 需要核查高星来源、许可证、commit 和借鉴边界时，读取[来源追踪](references/source-provenance.md)。

## 完成输出

每次完成结构工作时报告：

- 检测到的项目类型、技术栈、部署和仓库模式。
- 选中蓝图及其证据、适配与例外。
- 生成或保留的目录树和重要目录职责。
- 本轮文件放置决定及伴随测试/文档。
- 被保留的现有惯例。
- 审计状态、规则 ID、结构风险和下一步。

## 禁止合理化

| 借口 | 判定 |
| --- | --- |
| “先把文件放根目录，之后再整理” | 根目录堆积会固化为惯例；先路由再创建。 |
| “所有项目用一套树更统一” | 项目用途、部署和工作流不同；统一树是文档明确的失败场景。 |
| “现有结构不够理想，顺手重构” | 现有一致惯例优先；无关重组越界。 |
| “有 SKILL.md 就算完成” | 没有真实脚本、模板渲染、失败路径和 audit 证据时为 `BLOCK`。 |
| “smoke 能跑，所以结构合格” | 必须同时验证搭建期和运行期，并注入漂移验证失败门禁。 |

## 验证清单

- [ ] 新项目完成 `detect/选择 → scaffold → 文档/manifest → audit PASS`。
- [ ] 运行期完成 `suggest → 创建 → audit PASS`。
- [ ] React+FastAPI、TS Monorepo、科研三类主路径均真实验证。
- [ ] 新 React feature 与新编号科研 step 位置正确。
- [ ] 现有 `apps/packages` 仓库未被改成 `frontend/backend`，且无文件被自动移动。
- [ ] 根级混放、`misc/temp/common/utils`、`steps` 堆算法等失败场景返回非零状态和稳定规则 ID。
- [ ] `PROJECT_STRUCTURE.md` 与 `.project-structure.yaml` 无未替换占位符，重要目录都有职责。
- [ ] 所有适用工作流已接入结构门禁，生成式技能注册表已更新。
- [ ] Skill 校验、全量测试、fresh-agent 前向测试和反少实现审计均有证据。
