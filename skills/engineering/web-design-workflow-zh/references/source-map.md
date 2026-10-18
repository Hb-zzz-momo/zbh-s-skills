# Web Design Skill Source Map

## 选择结论

外部压缩包只作为按需能力库，不全量安装、不全量加载。项目约束和 `DESIGN.md` 始终高于外部 skill 的默认偏好。

| 来源 | Entry / Skill | 行数 | 使用方式 | 结论 |
|---|---|---:|---|---|
| `web-design-main.zip` | `web-design-main/SKILL.md` / `web-design` | 383 | 新建网站时生成 DESIGN.md、分析 PRD/URL/截图 | 核心设计规范来源 |
| `skills-main.zip` | `skills-main/skills/frontend-design/SKILL.md` / `frontend-design` | 56 | DESIGN.md 编码前做独特性、自我批判和 signature 检查 | 核心轻量审美门 |
| `taste-skill-main.zip` | `taste-skill-main/skills/taste-skill/SKILL.md` / `design-taste-frontend` | 1207 | 仅用于维护本工作流或专项深审，不在普通任务全量加载 | 规则过长，已提炼 Taste Gate |
| `taste-skill-main.zip` | `taste-skill-main/skills/redesign-skill/SKILL.md` / `redesign-existing-projects` | 179 | 现有项目先扫描、诊断、定点升级 | 改版分支主 skill |
| `taste-skill-main.zip` | `taste-skill-main/skills/imagegen-frontend-web/SKILL.md` | 988 | 明确要求图像先行时，在独立设计阶段使用 | 可选，不进入常规链 |
| `taste-skill-main.zip` | `taste-skill-main/skills/image-to-code-skill/SKILL.md` | 1229 | 已选定视觉稿后分析并实现 | 可选，与 imagegen 成对使用 |
| `taste-skill-main.zip` | `taste-skill-main/skills/gpt-tasteskill/SKILL.md` / `gpt-taste` | 75 | 高动效实验页才考虑 | 默认不选，强制 GSAP/Bento 等规则过硬 |
| `taste-skill-main.zip` | `taste-skill-main/skills/stitch-skill/SKILL.md` | 185 | 用户明确使用 Google Stitch 时 | 条件分支 |
| `garden-skills-main.zip` | `garden-skills-main/skills/web-design-engineer/SKILL.md` | 494 | 单文件 HTML、浏览器演示、可交互视觉产物 | 不替代正式产品工程流 |
| `skills-main.zip` | `skills-main/skills/webapp-testing/SKILL.md` | 96 | Playwright 本地测试 | 已有 `browser-testing-with-devtools`，不重复加载 |
| `skills-main.zip` | `skills-main/skills/web-artifacts-builder/SKILL.md` | 74 | Claude HTML artifact 打包 | 只用于 artifact，不用于普通网站 |
| `awesome-claude-design-main.zip` | `awesome-claude-design-main/README.md` | - | DESIGN.md 灵感目录 | 不是可执行 skill，只做参考索引 |

## 本地已安装能力

| Skill | Path | 职责 |
|---|---|---|
| `web-design-workflow-zh` | `skills/engineering/web-design-workflow-zh/` | 总控、分支、门禁 |
| `frontend-ui-engineering` | `skills/agent-skills-ao/frontend-ui-engineering/` | 组件、状态、响应式、可访问性、工程实现 |
| `browser-testing-with-devtools` | `skills/agent-skills-ao/browser-testing-with-devtools/` | 真实浏览器验证、控制台、网络、截图 |
| `performance-optimization` | `skills/agent-skills-ao/performance-optimization/` | 正式产品或性能回归时追加 |
| `code-review-and-quality` | `skills/agent-skills-ao/code-review-and-quality/` | 正式产品合并前审查 |

## 最小加载规则

### 新建网站

1. 读取 `web-design`。
2. 读取 56 行的 `frontend-design` 做设计批判。
3. 编码阶段切换到本地 `frontend-ui-engineering`。
4. 验收阶段切换到 `browser-testing-with-devtools`。

### 现有改版

1. 读取 `redesign-existing-projects`。
2. 更新当前 `DESIGN.md` 或生成差异规范。
3. 使用本地工程和浏览器 skills。

### 图像先行

1. 在独立阶段使用 `imagegen-frontend-web` 或本机 `imagegen`。
2. 确认视觉方向后再使用 `image-to-code`。
3. 从视觉稿反向固化 `DESIGN.md`，之后不再依赖图像猜测。

## 冲突优先级

```text
用户明确要求
> 当前项目技术栈和设计系统
> 项目 DESIGN.md / PRD
> 本工作流门禁
> 外部 skill 默认偏好
```

例如：外部 skill 反对 Lucide，但当前项目和上层规范要求使用 Lucide 时，沿用项目和上层规范；外部 skill 强制 GSAP，但页面只需轻量交互时，不安装 GSAP。

## 无效压缩包

根目录中多个约 130 字节的 `.zip` 不是有效压缩包，`ZipArchive` 会报 `End of Central Directory record could not be found`。它们不得进入工作流，需重新下载后再评估。
