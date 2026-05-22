# Skills 库路由优化工作流

> 目标：把 `C:\Users\zbh\.agents\skills` 从“技能清单”优化为“先路由、再加载、少量组合”的可执行系统。

## 前置条件

- 已有 `skills/README.md` 作为自动生成索引。
- 已有 `agent-skills-ao` 作为工程生命周期参考。
- 用户希望 Codex 能自如使用整个 skills 库，而不是每次靠聊天解释。

## 标准流程

### Step 1：盘点现有入口

- 读取 `skills/README.md`，确认场景分组、触发词、技能数量。
- 读取 `skills/.instructions.md`，检查维护规则是否可读。
- 读取 `agent-skills-ao/USAGE.zh-CN.md`，确认工程生命周期入口。
- 读取 `scripts/Update-SkillsReadme.ps1`，确认 README 是生成物。

完成标准：明确哪些文件是源头，哪些文件是生成物。

### Step 2：增加总控路由 skill

- 新增 `guardrail/skill-router-zh/SKILL.md`。
- 让它负责选择最少必要的 1-3 个 skill。
- 让它明确“不执行专业任务，只做路由，路由后切换对应 skill”。

完成标准：未来用户说“该用哪个 skill / 统筹 skills 库”时，有明确技能入口。

### Step 3：增加全仓库路由手册

- 新增 `SKILL_ROUTING.zh-CN.md`。
- 按领域、阶段、风险、常见组合组织。
- 提供可直接复制的调用提示。

完成标准：Codex 或用户能从一个文档快速判断 skill 组合。

### Step 4：修复维护说明

- 重写 `skills/.instructions.md`。
- 保留 README 自动同步规则。
- 增加路由优先、少量加载、编码规则。

完成标准：未来维护 skills 时不会只改 skill 文件而忘记 README 或路由入口。

### Step 5：接入 README 生成器

- 在 `Update-SkillsReadme.ps1` 中加入 `skill-router-zh` 的场景映射。
- 在 README 顶部生成 `Skill Routing Protocol`。
- 在目录树中显示 `SKILL_ROUTING.zh-CN.md`。
- 重新运行生成器。

完成标准：`skills/README.md` 能稳定再生，并保留路由入口。

### Step 6：验证

- 检查新增文件存在。
- 检查 README 中出现 `Skill Routing Protocol` 和 `skill-router-zh`。
- 检查 PowerShell 脚本仍保留 UTF-8 BOM。
- 检查中文文件无 `U+FFFD` 替换字符。

## 异常处理

- 如果 `.instructions.md` 或旧 skill 文件出现 mojibake，优先重写或修复源文件，再生成 README。
- 如果 README 直接手改丢失，重新运行 `Update-SkillsReadme.ps1`。
- 如果新增 skill 未出现在 README，检查 `scenarioBySkill` 映射和 frontmatter `name`。

## 可迁移建议

后续新增任意技能时，都要回答三个问题：

1. 它属于哪个场景分组？
2. 它应该和哪些 skill 搭配？
3. 它是否应该进入 `SKILL_ROUTING.zh-CN.md` 的常见组合？
