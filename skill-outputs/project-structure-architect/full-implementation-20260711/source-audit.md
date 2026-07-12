# 高星来源下载与借鉴审计

快照时间：2026-07-11 21:13:45 +08:00。Star 为 GitHub API 统一查询快照，会随时间变化。第三方内容只下载到被 Git 忽略的 `.tmp/project-structure-architect-upstream/` 研究区；未执行任何上游脚本，未把上游完整 Skill 复制进正式交付目录。

| 来源 | Star | 许可证 | 固定 commit | 本地只读快照 | 借鉴内容 | 明确不借鉴 |
| --- | ---: | --- | --- | --- | --- | --- |
| [github/awesome-copilot](https://github.com/github/awesome-copilot/tree/main/skills/folder-structure-blueprint-generator) | 36,441 | MIT | `30472ecf0fe34cc561df958c08501ecc5ca80ea4` | `.tmp/project-structure-architect-upstream/awesome-copilot/skills/folder-structure-blueprint-generator/` | 多技术栈、Monorepo、微服务标志；目录职责、放置、命名、构建输出和扩展检查清单 | 不复制其长提示词；不把“只生成说明文档”冒充结构 enforcement |
| [vercel/turborepo](https://github.com/vercel/turborepo/tree/main/skills/turborepo) | 30,700 | MIT | `de6a0d3ff75ea2a13695be63b715f92df4c9eabd` | `.tmp/project-structure-architect-upstream/turborepo/skills/turborepo/` | `apps/` 为可部署单元、`packages/` 为共享包；决策树与按需 reference；包边界和禁止跨包深链 | 规则只用于 TS Monorepo profile，不提升为所有项目的统一根结构 |
| [agentskills/agentskills](https://github.com/agentskills/agentskills) | 22,904 | Apache-2.0（代码）/ CC-BY-4.0（文档） | `38a2ff82958afee88dadf4831509e6f7e9d8ef4e` | `.tmp/project-structure-architect-upstream/agentskills/` | `SKILL.md + scripts + references + assets` 包结构、渐进式披露、可执行脚本与验证原则 | 不引入规范未要求的 frontmatter 字段，不复制站点资源 |
| [microsoft/skills](https://github.com/microsoft/skills/tree/main/.github/plugins/deep-wiki/skills/wiki-agents-md) | 2,727 | MIT | `c33193b1b2dd14d5946e3c6213fd095ffa5b31df` | `.tmp/project-structure-architect-upstream/microsoft-skills/.github/plugins/deep-wiki/skills/wiki-agents-md/` | 先读真实 manifest/config，再生成 root/nested `AGENTS.md`；最近作用域优先；已存在文件不覆盖；禁止 TODO/占位/臆造命令 | 不生成与真实项目无关的通用长文，不覆盖现有 `AGENTS.md` |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 77,154 | MIT | `4e8bd9fde4a38cd009053e649f4cdc7cd36b568b` | `.tmp/project-structure-architect-upstream/addyosmani-agent-skills/docs/skill-anatomy.md` | 主 Skill 保持短小、详细知识按需加载、脚本输出结构化、验证项必须有证据 | 不复制其 Bash 专属约定到本 Python/Windows 交付，不无条件引入其他工程工作流 |

## 目录蓝图的数据源

以下仓库不作为可执行 Skill 安装，只用于核对各 profile 的领域惯例：

| 来源 | Star 快照 | 许可证 | 仅借鉴内容 |
| --- | ---: | --- | --- |
| [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | 44,169 | MIT | 独立 `frontend/`、`backend/` 部署边界 |
| [alan2207/bulletproof-react](https://github.com/alan2207/bulletproof-react) | 35,503 | MIT | React `app/features/components/lib` 分层及 feature ownership |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 30,670 | MIT（仓库；各 Skill 仍需单独核验） | 科研多步骤输入、输出与工具链记录方式 |
| [kedro-org/kedro](https://github.com/kedro-org/kedro) | 10,911 | Apache-2.0 | 大型数据流水线的 pipeline/node 分工 |
| [drivendataorg/cookiecutter-data-science](https://github.com/drivendataorg/cookiecutter-data-science) | 9,938 | MIT | `raw/interim/processed/external` 数据生命周期与编号 notebook |

## 供应链与许可证结论

- `PASS`：正式 skill 为本地重写实现，只吸收抽象规则和目录惯例，没有 vendoring 第三方源码。
- `PASS`：每个直接下载来源均固定到 commit，并记录仓库级许可证。
- `PASS`：研究快照位于 `.tmp/`，`.gitignore` 已排除该目录。
- `CAUTION`：Star 仅是流行度快照，不代表质量或安全保证；未来更新来源时必须重新核验 commit 与许可证。
