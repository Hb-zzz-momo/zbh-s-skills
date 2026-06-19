# Source Map

本技能只做编排。需要深入规则时，按阶段读取最小必要来源，不要一次性加载全部压缩包。

## Local Sources

| Source | Local path | Read when |
|---|---|---|
| KAOPU-XiaoPu/web-design | `C:\Users\zbh\.agents\web-design-main.zip` | 需要生成或修订 `DESIGN.md`、参考 URL/截图/PRD 推导设计规范 |
| web-design template | `web-design-main/references/design-md-template.md` in the zip | 需要完整 `DESIGN.md` 模板 |
| Leonxlnx/taste-skill | `C:\Users\zbh\.agents\taste-skill-main.zip` | 需要 Design Read、三档审美参数、anti-slop 审查 |
| taste redesign skill | `taste-skill-main/skills/redesign-skill/SKILL.md` in the zip | 现有项目 UI 改版、先审计再修 |
| local frontend engineering | `C:\Users\zbh\.agents\skills\agent-skills-ao\frontend-ui-engineering\SKILL.md` | 组件结构、状态、响应式、可访问性、设计系统实现 |
| Vercel frontend-design zip copy | `C:\Users\zbh\.agents\skills-main.zip`, `skills-main/skills/frontend-design/SKILL.md` | 需要补充“独特视觉设计、非模板化选择”的设计批判视角 |

## Remote Sources

| Source | URL | Read when |
|---|---|---|
| Vercel agent skill wrapper | `https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/web-design-guidelines/SKILL.md` | 需要确认 Vercel skill 的调用方式 |
| Vercel web interface guidelines | `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` | 最终验收前；优先用最新版本 |

## Loading Policy

1. 先读当前项目的 `DESIGN.md`、PRD、截图、代码和依赖。
2. 只有当当前项目缺少设计规范时，读取 `web-design` 的 `SKILL.md` 和 `design-md-template.md`。
3. 只有当页面容易模板化、AI 味明显或需要审美方向判断时，读取 `taste-skill`。
4. 编码时读取本地 `frontend-ui-engineering`，按项目已有技术栈实现。
5. 验收时联网读取 Vercel 最新 `command.md`；失败则使用本地 `acceptance-checklist.md`。

## Zip Handling Notes

部分根目录压缩包可能不是有效 zip 或下载不完整。不要依赖文件名猜测内容；读取前先用 ZipArchive/Expand-Archive 验证。
