# 借鉴来源与边界

以下为 2026-07-11 21:13:45 +08:00 通过 GitHub API 统一核验的快照。Star 会变化；提交 SHA 固定本轮参考版本。许可证字段为仓库元数据中的 SPDX 标识，不替代逐文件许可证核查。

| 仓库 | URL | Stars | License | Commit | 本 Skill 的借鉴边界 |
|---|---|---:|---|---|---|
| `github/awesome-copilot` | https://github.com/github/awesome-copilot | 36,441 | MIT | `30472ecf0fe34cc561df958c08501ecc5ca80ea4` | 仅借鉴 folder-structure skill 的项目探测维度、树说明和扩展模板思想；未复制原文 |
| `vercel/turborepo` | https://github.com/vercel/turborepo | 30,700 | MIT | `de6a0d3ff75ea2a13695be63b715f92df4c9eabd` | 仅借鉴 `apps/`/`packages/` 边界、内部包与渐进式 references 组织 |
| `K-Dense-AI/scientific-agent-skills` | https://github.com/K-Dense-AI/scientific-agent-skills | 30,670 | MIT | `4d97e293dc6f604fb6b63dcd49b9028df413d65b` | 仅借鉴科研工作流输入、输出、工具链分阶段记录方式 |
| `agentskills/agentskills` | https://github.com/agentskills/agentskills | 22,904 | Apache-2.0 | `38a2ff82958afee88dadf4831509e6f7e9d8ef4e` | 仅遵循 Skill 的 `SKILL.md`、`scripts/`、`references/`、`assets/` 渐进式结构 |
| `microsoft/skills` | https://github.com/microsoft/skills | 2,727 | MIT | `c33193b1b2dd14d5946e3c6213fd095ffa5b31df` | 仅借鉴 wiki-agents-md 的子项目识别及嵌套 `AGENTS.md` 规则继承思想 |
| `addyosmani/agent-skills` | https://github.com/addyosmani/agent-skills | 77,154 | MIT | `4e8bd9fde4a38cd009053e649f4cdc7cd36b568b` | 仅借鉴主流程精简、详细知识按需加载、验证门禁与评测思路 |
| `fastapi/full-stack-fastapi-template` | https://github.com/fastapi/full-stack-fastapi-template | 44,169 | MIT | `4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2` | 仅借鉴前后端独立根目录和局部依赖/测试/文档边界 |
| `alan2207/bulletproof-react` | https://github.com/alan2207/bulletproof-react | 35,503 | MIT | `9506629ed003a561c6627735480cce4994244bb4` | 仅借鉴 feature-based 前端分层及共享/局部边界 |
| `kedro-org/kedro` | https://github.com/kedro-org/kedro | 10,911 | Apache-2.0 | `d3b46f3b69876674de99c254133d86d0564c612b` | 仅借鉴 pipeline 节点、执行关系、配置分离和可复现性原则 |
| `drivendataorg/cookiecutter-data-science` | https://github.com/drivendataorg/cookiecutter-data-science | 9,938 | MIT | `0f6b163cdbe3918a2c65ab57ad9fefda93976d9e` | 仅借鉴 `raw`/`interim`/`processed` 数据生命周期与 Notebook 编号思想 |
| `snakemake/snakemake` | https://github.com/snakemake/snakemake | 2,826 | MIT | `1a2774645a599d6c7d0589a048b64023b360c7d3` | 仅借鉴显式输入输出依赖和可复现工作流边界 |

## 直接读取的 Skill 文件

本轮按上表固定提交从 `raw.githubusercontent.com` 下载到内存并读取以下原文，未将上游文件写入项目。SHA-256 用于证明所读内容版本：

| 来源文件 | 固定版本 URL | SHA-256 | 实际提取的思想 |
|---|---|---|---|
| awesome-copilot `folder-structure-blueprint-generator/SKILL.md` | https://raw.githubusercontent.com/github/awesome-copilot/30472ecf0fe34cc561df958c08501ecc5ca80ea4/skills/folder-structure-blueprint-generator/SKILL.md | `6e0c362502ea65b3c929fb02baecaf6da2420352c4aa27eebbd2b89643198be3` | 自动探测、结构总览、ASCII 树、目录职责与文件位置模式 |
| Turborepo `skills/turborepo/SKILL.md` | https://raw.githubusercontent.com/vercel/turborepo/de6a0d3ff75ea2a13695be63b715f92df4c9eabd/skills/turborepo/SKILL.md | `9ef67cf4b2e93a20b3932326910b789baa763cc53d46d68166c344d4de1ba2d9` | 快速决策树、应用/包边界、包级责任和按需引用 |
| Microsoft `wiki-agents-md/SKILL.md` | https://raw.githubusercontent.com/microsoft/skills/c33193b1b2dd14d5946e3c6213fd095ffa5b31df/.github/plugins/deep-wiki/skills/wiki-agents-md/SKILL.md | `0345a27f116f3217e121f0ff110f8e92ac9f9c72b1fd7b3e8c61639550db3e63` | 仅在缺失时生成、重要子目录识别、嵌套规则和跳过生成目录 |

## 使用约束

- 本 Skill 的中文规则、蓝图 JSON、模板和脚本接口均为针对《文件树组织架构.md》重新设计的实现。
- 不复制上游长段说明、代码或模板；目录名等事实性惯例不构成对具体表达的复制。
- 上游许可证不自动覆盖本仓库；若未来直接引入代码或大段内容，必须单独保留许可证、版权声明和文件级来源。
- Star 仅用于说明参考项目的社区可见度，不作为规则正确性的证据；最终规则仍以用户要求、现有仓库约定和可运行验收为准。
